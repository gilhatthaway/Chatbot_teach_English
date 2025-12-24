# Hệ Thống Chatbot Dạy Tiếng Anh

## Tổng Quan Hệ Thống

Đây là hệ thống dạy tiếng Anh được hỗ trợ bởi trí tuệ nhân tạo (AI), kết hợp khả năng chatbot với các tính năng quản trị cho người dùng và bài học. Hệ thống cung cấp trải nghiệm học tập tương tác thông qua trò chuyện văn bản, tương tác giọng nói và các bài học có cấu trúc.

### ✨ Tính Năng Chính

**1. Chatbot Thông Minh với Memory & Context**
- 🧠 Semantic Search: Tìm kiếm ngữ cảnh liên quan dùng FAISS
- 💾 Persistent Memory: Lưu trữ lịch sử tự động trên disk
- 📝 Multi-turn Conversation: Hiểu context từ các tin nhắn trước
- 🚀 Auto-Summarize: Tự động nén lịch sử cũ để tiết kiệm token

**2. Voice Interaction**
- 🎙️ Speech Recognition: Chuyển giọng nói thành text (Google SR)
- 🔊 Text-to-Speech: Đọc response bằng giọng nói (gTTS)
- 💬 Context-Aware Voice: Sử dụng memory khi trả lời

**3. Lesson Generation**
- 📚 AI-Generated Lessons: Tạo bài học tự động từ chủ đề
- 📊 Lesson History: Lưu trữ và quản lý lịch sử bài học
- 📈 Progress Tracking: Theo dõi tiến độ học tập

**4. Exam Management**
- ✏️ Create/Update Exams: Quản lý bài kiểm tra
- 📋 Auto-Grade: Chấm điểm tự động
- 📊 Results Analytics: Thống kê kết quả

**5. Admin Dashboard**
- 👥 User Management: Quản lý người dùng
- 📝 Lesson Management: Quản lý bài học
- 📊 Query Analytics: Phân tích dữ liệu


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

   # quên mật khẩu có SMTP_EMAIL, SMTP_PASS 

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
- `memory.py`: Advanced Memory Management với FAISS Semantic Search

## Memory System - Ngữ Cảnh & Lịch Sử Thông Minh

### Cách Hoạt Động

Chatbot sử dụng AdvancedConversationMemory để:

1. **Giữ Lịch Sử Gần Nhất**: Tự động lưu 10 tin nhắn gần nhất
2. **Semantic Search**: Tìm 5 tin nhắn liên quan nhất dùng FAISS
3. **Auto-Summarize**: Nén tin nhắn cũ sau 30 tin nhắn
4. **Persistent Storage**: Lưu vào disk để khôi phục sau khi restart

### API Endpoints

```bash
# Lấy thống kê memory
GET /memory/stats/<id_nguoi_dung>

# Lấy toàn bộ lịch sử
GET /memory/history/<id_nguoi_dung>

# Xóa memory (reset)
DELETE /memory/clear/<id_nguoi_dung>
```

**Chi Tiết đầy đủ**: Xem [MEMORY_INTEGRATION.md](MEMORY_INTEGRATION.md)

## Kiến Trúc Hệ Thống

```
agent.py
├─ /chat (POST)              → Chat text với context
├─ /voice (POST)             → Chat voice với context
├─ /generate/lesson (POST)   → Tạo bài học AI
├─ /memory/stats (GET)       → Xem thống kê memory
├─ /memory/history (GET)     → Lấy lịch sử
└─ /memory/clear (DELETE)    → Xóa memory

memory.py
├─ AdvancedConversationMemory
├─ FAISS Indexes
├─ Semantic Search
└─ Auto-Summarize

save_mysql.py
├─ Database Operations
├─ Chat History (DB)
├─ Lesson Management
└─ Exam Management
```

######### CHẠY DATA###
Chạy file save_mysql trước rồi chạy các migrat
