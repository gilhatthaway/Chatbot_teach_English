# Hệ Thống Chatbot Dạy Tiếng Anh

## Tổng Quan Hệ Thống

Đây là hệ thống dạy tiếng Anh được hỗ trợ bởi trí tuệ nhân tạo (AI), kết hợp khả năng chatbot với các tính năng quản trị cho người dùng và bài học. Hệ thống cung cấp trải nghiệm học tập tương tác thông qua trò chuyện văn bản, tương tác giọng nói và các bài học có cấu trúc.


## Cài Đặt và Thiết Lập

1. **Yêu Cầu Hệ Thống**
   - Python 3.x
   - MySQL Installer
   - Các gói Python cần thiết (xem requirements.txt)
   - Truy cập API của Google Gemini và lấy key: https://aistudio.google.com/api-keys

2. **Thiết Lập Môi Trường**
   ```bash
   # Sao chép kho lưu trữ
   git clone https://github.com/Hoang472003/Hoc_tieng_Anh_voi_AIchatbot

   # Cài đặt các gói phụ thuộc
   pip install -r requirements.txt

   # Cấu hình cơ sở dữ liệu
   # Chỉnh sửa config_py.py với thông tin đăng nhập MySQL của bạn

   # Cấu hình biến môi trường
   # Tạo file .env và thêm API vào biên môi trường như sau:
   GEMINI_API_KEY = "YOUR_API_KEY"


   ```

3. **Khởi Tạo Cơ Sở Dữ Liệu**
   ```python
   # Hệ thống sẽ tự động:
   - Tạo cơ sở dữ liệu cần thiết
   - Khởi tạo các bảng
   - Tạo tài khoản admin mặc định
   ```

4. **Khởi Động Ứng Dụng**
   ```bash
   python agent.py
   ```

## Cấu Hình

Hệ thống sử dụng các tệp cấu hình sau:
- `config_py.py`: Cài đặt cơ sở dữ liệu và hệ thống
- `prompt.py`: Mẫu Rule hội thoại cho từng config AI
- `save_mysql.py`: Thao tác với cơ sở dữ liệu



######### CHẠY DATA###
Chạy file save_mysql trước rồi chạy các migrat
