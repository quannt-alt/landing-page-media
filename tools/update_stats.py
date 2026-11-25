#!/usr/bin/env python3
"""Cập nhật số liệu trong landing/index.html từ dữ liệu dashboard.

Cách dùng (chạy ở bất kỳ đâu):
    python3 landing/tools/update_stats.py [đường-dẫn/agent-state.json]

Mặc định đọc ~/code/media/dashboard/data/agent-state.json.
Script thay nội dung các phần tử có data-k="..." (số tổng), data-v="kênh:id" (lượt xem
từng ảnh bìa), khối <script id="series"> (biểu đồ) và băng chữ giữa <!--ticker--> … <!--/ticker-->.
Số không có trong dữ liệu (fanpage 1.200+) giữ nguyên, sửa tay trong index.html.
"""
import datetime as dt
import html
import json
import re
import statistics
import sys
from pathlib import Path

LANDING = Path(__file__).resolve().parent.parent
PAGE = LANDING / "index.html"
DEFAULT_SRC = Path.home() / "code/media/dashboard/data/agent-state.json"
VN = dt.timezone(dt.timedelta(hours=7))
CH_CLASS = {"visual-stem": "c-vs", "english-ko-kho": "c-ekk", "voz-story": "c-voz"}


def vn(n):
    return f"{int(round(n)):,}".replace(",", ".")


def parse_t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    state = json.loads(src.read_text(encoding="utf-8"))
    items = state["items"]

    yt = {}          # key -> lượt xem YouTube của video đã đăng
    posted = []      # (thời điểm đăng, kênh, tiêu đề)
    tt_total = 0
    photos = 0
    latest = None
    for key, x in items.items():
        posts = x.get("posts") or {}
        metrics = x.get("metrics") or {}
        if x.get("kind") == "photo":
            if (posts.get("facebook") or {}).get("status") == "posted":
                photos += 1
            continue
        p = posts.get("youtube") or {}
        if p.get("status") != "posted":
            continue
        m = metrics.get("youtube") or {}
        yt[key] = m.get("views") or 0
        if m.get("at"):
            t = parse_t(m["at"])
            latest = t if latest is None or t > latest else latest
        posted.append((p.get("postedAt") or p.get("at") or "", x["channel"], x.get("title", "")))
        if (posts.get("tiktok") or {}).get("status") == "posted":
            tt_total += (metrics.get("tiktok") or {}).get("views") or 0

    def ch(c):
        return {k: v for k, v in yt.items() if k.startswith(c + ":")}

    vs, ekk, voz = ch("visual-stem"), ch("english-ko-kho"), ch("voz-story")
    voz_long = [k for k in voz if "-S" not in k.split(":", 1)[1]]

    # Chuỗi cộng dồn theo ngày (giờ VN), 30 ngày gần nhất
    end = (latest or dt.datetime.now(dt.timezone.utc)).astimezone(VN).date()
    days = [end - dt.timedelta(days=d) for d in range(30, -1, -1)]
    hist = state.get("metricsHistory", {})
    rows = {k: sorted((parse_t(r[0]), r[1]) for r in (hist.get(k, {}).get("youtube") or []) if r[1] is not None)
            for k in yt}
    values = []
    for d in days:
        cutoff = dt.datetime.combine(d, dt.time(23, 59, 59), VN)
        tot = 0
        for r in rows.values():
            last = None
            for t, v in r:
                if t <= cutoff:
                    last = v
                else:
                    break
            tot += last or 0
        values.append(tot)
    labels = [d.strftime("%d/%m") for d in days]

    total = sum(yt.values())
    k = {
        "yt_total": vn(total),
        "videos_total": vn(len(yt)),
        "tt_total": vn(tt_total),
        "growth_30d": "+" + vn(values[-1] - values[0]),
        "series_first": vn(values[0]),
        "vs_n": vn(len(vs)), "vs_yt": vn(sum(vs.values())),
        "vs_over300": f"{sum(v > 300 for v in vs.values())}/{len(vs)}",
        "vs_median": vn(statistics.median(vs.values())),
        "ekk_n": vn(len(ekk)), "ekk_yt": vn(sum(ekk.values())), "ekk_top": vn(max(ekk.values())),
        "ekk_photos": vn(photos),
        "voz_long": vn(len(voz_long)), "voz_short": vn(len(voz) - len(voz_long)),
        "voz_yt": vn(sum(voz.values())),
        "voz_over300": f"{sum(v > 300 for v in voz.values())}/{len(voz)}",
        "as_of": end.strftime("%d/%m/%Y"),
    }

    page = PAGE.read_text(encoding="utf-8")

    def sub_k(m):
        key = m.group(3)
        return m.group(1) + k[key] + m.group(4) if key in k else m.group(0)

    page = re.sub(r'(<(\w+)\b[^>]*\bdata-k="([\w]+)"[^>]*>)[^<]*(</\2>)', sub_k, page)

    missing = []

    def sub_v(m):
        key = m.group(3)
        if key not in yt:
            missing.append(key)
            return m.group(0)
        return m.group(1) + vn(yt[key]) + m.group(4)

    page = re.sub(r'(<(\w+)\b[^>]*\bdata-v="([^"]+)"[^>]*>)[^<]*(</\2>)', sub_v, page)

    series = json.dumps({"labels": labels, "values": values}, separators=(",", ":"))
    page = re.sub(r'(<script id="series" type="application/json">).*?(</script>)',
                  lambda m: m.group(1) + series + m.group(2), page, flags=re.S)

    posted.sort(reverse=True)
    li = [f'        <li class="{CH_CLASS[c]}">{html.escape(t)}</li>' for _, c, t in posted]
    dup = [s.replace("<li ", '<li aria-hidden="true" ', 1) for s in li]  # bản sao để băng chữ chạy liền mạch
    page = re.sub(r"<!--ticker-->.*?<!--/ticker-->",
                  lambda m: "<!--ticker-->\n" + "\n".join(li + dup) + "\n<!--/ticker-->", page, flags=re.S)

    PAGE.write_text(page, encoding="utf-8")
    print(f"Đã cập nhật {PAGE} (số liệu tới {k['as_of']})")
    for key in ("yt_total", "videos_total", "growth_30d", "vs_yt", "ekk_yt", "voz_yt", "tt_total", "ekk_photos"):
        print(f"  {key:13} {k[key]}")
    if missing:
        print("  Cảnh báo: không tìm thấy video", ", ".join(missing))


if __name__ == "__main__":
    main()
