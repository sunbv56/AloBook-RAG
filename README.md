# AloBook AI Chatbot 🤖📖

AloBook AI Chatbot là một hệ thống chatbot bán hàng và hỗ trợ chăm sóc khách hàng tự động được tích hợp AI thế hệ mới, tối ưu hóa riêng cho cửa hàng sách trực tuyến **AloBook.vn**.

Hệ thống kết hợp sự linh hoạt của mô hình ngôn ngữ lớn (Google Gemini thông qua n8n workflow) cùng khả năng phản hồi dự phòng nhanh chóng thông qua máy chủ cục bộ (local fallback).

---

## 🌟 Tính năng Nổi bật

*   **Tư vấn Sản phẩm (Sách):** Hỗ trợ tìm kiếm sách theo tên, thể loại hoặc nội dung mô tả trực tiếp từ cơ sở dữ liệu sản phẩm.
*   **Tra cứu Đơn hàng Tự động:** Khách hàng chỉ cần nhập mã đơn hàng (định dạng `ABxxxxx`) để nhận thông tin thời gian thực về trạng thái đơn hàng (Đã thanh toán, Đang giao, Đã hủy, v.v.), địa chỉ nhận hàng, và tổng thanh toán.
*   **Thu thập Khách hàng Tiềm năng (Lead Generation):** Form tích hợp trực tiếp trong khung chat giúp thu thập thông tin liên hệ (Họ tên, Email, Số điện thoại) của khách hàng trước khi bắt đầu cuộc trò chuyện.
*   **Chuyển giao cho Nhân viên hỗ trợ (Escalation):** Tự động nhận diện nhu cầu gặp tư vấn viên trực tiếp của khách hàng để chuyển hướng phiên chat.
*   **Rate Limiting (Chống Spam):** Giới hạn tối đa 10 tin nhắn/phút trên mỗi địa chỉ IP để bảo vệ hệ thống khỏi tấn công spam.
*   **Chế độ Dự phòng Thông minh (Local Fallback):** Nếu n8n webhook (cloud) ngoại tuyến hoặc chưa kích hoạt, chatbot sẽ tự động chuyển sang chế độ phản hồi dựa trên tập luật cục bộ ngay lập tức.

---

## 🛠️ Công nghệ Sử dụng

### Backend (Máy chủ)
*   **Python 3.x**
*   **Flask:** Framework web gọn nhẹ dùng để phục vụ frontend và cung cấp các API endpoint.
*   **HTTPX:** Thư viện client HTTP bất đồng bộ dùng để kết nối với Webhook n8n một cách tối ưu.
*   **Python-dotenv:** Quản lý cấu hình thông qua file môi trường `.env`.

### Frontend (Giao diện)
*   **HTML5 / Vanilla CSS:** Thiết kế giao diện hiện đại với phong cách Premium (Vibrant colors, dark mode support, glassmorphism, và micro-animations).
*   **Vanilla JavaScript:** Xử lý luồng hội thoại, gọi API backend, kiểm tra biểu thức chính quy (regex) và tương tác động.

### Tích hợp & Tự động hóa
*   **n8n Webhook:** Chuyển tiếp tin nhắn và xử lý logic AI Agent trên Cloud.

---

## 📂 Cấu trúc Thư mục

```text
├── main.py              # File chạy chính của server Backend (Flask)
├── Procfile             # File cấu hình chạy trên Render/Heroku
├── requirements.txt     # Danh sách các thư viện Python phụ thuộc
├── .env                 # File chứa biến môi trường (Webhook URL, Auth)
├── static/              # Thư mục chứa tài nguyên tĩnh của giao diện
│   ├── index.html       # Giao diện trang chủ cửa hàng & widget chat
│   ├── style.css        # Định nghĩa thiết kế giao diện & hiệu ứng động
│   └── app.js           # Bộ điều khiển logic chatbot phía Client
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy Cục bộ

### Bước 1: Clone kho lưu trữ về máy cá nhân
```bash
git clone https://github.com/sunbv56/Chatbot-SupportCus.git
cd Chatbot-SupportCus
```

### Bước 2: Tạo môi trường ảo và cài đặt thư viện
```bash
# Tạo môi trường ảo (venv)
python -m venv venv

# Kích hoạt môi trường ảo
# Trên Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Trên macOS/Linux:
source venv/bin/activate

# Cài đặt các thư viện yêu cầu
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` ở thư mục gốc của dự án với các thông tin sau:
```ini
N8N_WEBHOOK_URL=https://sunbv56.app.n8n.cloud/webhook/alobook-webhook
N8N_USERNAME=your_n8n_username
N8N_PASSWORD=your_n8n_password
PORT=8000
HOST=0.0.0.0
```

### Bước 4: Khởi động máy chủ cục bộ
```bash
python main.py
```
Sau đó truy cập trình duyệt tại địa chỉ: `http://localhost:8000` để trải nghiệm.

---

## ☁️ Hướng dẫn Triển khai (Deployment)

### 1. Triển khai Backend trên Render
*   Tạo Web Service mới trên **Render**.
*   Liên kết với kho lưu trữ GitHub của bạn.
*   Cấu hình các trường:
    *   **Runtime:** `Python`
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `gunicorn main:app` (hoặc cấu hình tự động nhận diện từ `Procfile`).
*   Thêm các biến môi trường tại phần **Environment** tương tự như file `.env`.

### 2. Cấu hình Webhook trên n8n
*   Đảm bảo luồng workflow n8n của bạn đã được kích hoạt (**Active**).
*   URL nhận tin nhắn phải khớp với URL cấu hình trong biến môi trường `N8N_WEBHOOK_URL` của server Flask.