# Tông Quân Studio — landing page

Trang giới thiệu 3 kênh Man Math (Visual STEM), English Ko Khó, VOZ Story.
HTML/CSS/JS thuần, không cần build. Mọi thứ nằm trong thư mục này:

```
landing/
├── index.html              trang duy nhất (CSS + JS viết sẵn bên trong)
├── assets/                 ảnh bìa, logo (WebP)
├── vercel.json             cấu hình Vercel (cache ảnh 7 ngày)
└── tools/update_stats.py   cập nhật số liệu từ dashboard
```

## Xem thử ở máy
```bash
python3 -m http.server 8000   # mở http://localhost:8000
```

## Deploy lên Vercel (qua GitHub)
Repo này chính là thư mục gốc của trang, không cần build.

1. Trên vercel.com → **Add New → Project** → chọn repo này trên GitHub.
2. Framework Preset: **Other**. Root Directory: để mặc định (`./`). Build Command: để trống.
3. Bấm **Deploy**. Từ đó, mỗi lần `git push` lên nhánh `main`, Vercel tự deploy lại.

## Cập nhật số liệu
```bash
python3 tools/update_stats.py                       # đọc ~/code/media/dashboard/data/agent-state.json
python3 tools/update_stats.py /đường/dẫn/agent-state.json
```
Script điền lại: tổng lượt xem, số video, tăng trưởng 30 ngày, số liệu từng kênh, lượt xem trên
từng ảnh bìa, biểu đồ cộng dồn và băng chữ tên video. Sau đó commit và `git push` là Vercel tự deploy lại.

Không lấy được từ dữ liệu, cần sửa tay trong `index.html`: số người theo dõi fanpage (1.200+),
2 phát hiện trong mục "Sáng tạo theo số liệu" (lấy từ báo cáo tuần), và việc chọn 6 video nổi bật mỗi kênh.

## Chuyển động
Mọi hiệu ứng tắt khi người xem bật "giảm chuyển động" trong hệ điều hành. Hiệu ứng hiện dần theo
cuộn trang dùng CSS scroll-driven animation (Chrome, Edge, Safari mới); trình duyệt khác vẫn hiện đủ nội dung.
