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

### Yêu Cầu Hệ Thống
- Python 3.8+
- MySQL 5.7+ hoặc 8.0
- Truy cập API của Google Gemini: https://aistudio.google.com/api-keys
- (Tùy chọn) TURN/STUN server cho WebRTC: https://www.twilio.com/stun-servers hoặc tự cấu hình

### 1. Clone Dự Án

```bash
git clone https://github.com/Hoang472003/Hoc_tieng_Anh_voi_AIchatbot
cd Hoc_tieng_Anh_voi_AIchatbot
```

### 2. Cài Đặt Python Dependencies

```bash
python -m venv venv
# Trên Windows:
venv\Scripts\activate
# Trên macOS/Linux:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Cấu Hình Cơ Sở Dữ Liệu

Cài đặt MySQL và đảm bảo nó đang chạy. Sau đó tạo file `.env`:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với thông tin MySQL của bạn:

```env
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=your-password
DB_NAME=aichat2

# Google Gemini API Key
GEMINI_API_KEY=your-gemini-api-key-here

# SMTP Configuration (for OTP and notifications)
SMTP_EMAIL=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=10
SMTP_RETRY_COUNT=3

# Admin Notifications
ADMIN_NOTIFICATION_EMAIL=admin@example.com
ADMIN_NOTIFICATION_WEBHOOK=

# WebRTC ICE Servers (STUN/TURN)
WEBRTC_ICE_SERVERS=[{"urls":["stun:stun.l.google.com:19302"]}]
# For TURN (production):
# WEBRTC_ICE_SERVERS=[{"urls":["turn:your-turn-server.com:3478"],"username":"user","credential":"pass"}]

# Logging Level
LOG_LEVEL=INFO
```

**Lưu ý SMTP:**
- Nếu dùng Gmail, tạo [App Password](https://myaccount.google.com/apppasswords)
- Port 587 = TLS (SMTP_USE_TLS=true), Port 465 = SSL (SMTP_USE_SSL=true)

### 4. Khởi Tạo Database

Chương trình sẽ tự động khởi tạo bảng khi khởi động:

```bash
python agent.py
```

Nó sẽ:
- Tạo database `aichat2`
- Khởi tạo tất cả các bảng cần thiết
- Tạo tài khoản admin mặc định: `admin / 123`

### 5. Chạy Ứng Dụng

```bash
python agent.py
```

Mở trình duyệt và truy cập: `http://localhost:5000`

---

## Biến Môi Trường (Secrets)

Tất cả biến môi trường được đọc từ file `.env`:

| Biến | Mô Tả | Bắt Buộc |
|------|-------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `SMTP_EMAIL` | Email gửi OTP/thông báo | ✅ |
| `SMTP_PASS` | Mật khẩu app email | ✅ |
| `SMTP_HOST` | SMTP server (ví dụ: smtp.gmail.com) | ✅ |
| `SMTP_PORT` | SMTP port (587 cho TLS, 465 cho SSL) | ✅ |
| `ADMIN_NOTIFICATION_EMAIL` | Email nhận thông báo admin | ❌ |
| `ADMIN_NOTIFICATION_WEBHOOK` | Webhook URL (Slack/Teams) | ❌ |
| `WEBRTC_ICE_SERVERS` | JSON danh sách STUN/TURN | ❌ |
| `LOG_LEVEL` | DEBUG\|INFO\|WARNING\|ERROR | ❌ |

---

## Deployment

### Gunicorn (Production)

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker agent:app
```

### Docker (Tùy chọn)

Tạo `Dockerfile`:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "agent:app"]
```

```bash
docker build -t chatbot-teach .
docker run -p 5000:5000 --env-file .env chatbot-teach
```

### Environment Variables Trên Server

Thay vì `.env`, set env vars trực tiếp:

```bash
export GEMINI_API_KEY="your-key"
export SMTP_EMAIL="your-email@gmail.com"
export SMTP_PASS="your-password"
# ... các biến khác
python agent.py
```

Hoặc dùng `.env` file và chắc chắn nó không commit vào git.

---

## Testing

### Local Smoke Tests

```bash
# Test messaging (SQLite fallback nếu MySQL unavailable)
python scripts/test_messages.py

# Test reports -> infractions -> auto-ban flow
python scripts/test_reports.py

# Test Socket.IO messaging
python scripts/test_socketio.py
```

### CI/CD (GitHub Actions)

CI tự động chạy khi push hoặc pull request:
- Kiểm tra syntax Python
- Chạy smoke tests
- Tự động test với MySQL service (nếu MySQL_* secrets có sẵn)

---

## Troubleshooting

### Lỗi Kết Nối MySQL

```
Error: Connection refused
```

**Giải pháp:**
- Đảm bảo MySQL đang chạy: `mysql -u root -p`
- Kiểm tra `DB_HOST`, `DB_USER`, `DB_PASS` trong `.env`
- Nếu MySQL chạy trên port khác (không phải 3306), thêm `DB_PORT` vào `.env`

### Lỗi SMTP / Email không gửi được

```
Error sending email: Authentication failed
```

**Giải pháp:**
- Xác nhận `SMTP_EMAIL` và `SMTP_PASS` đúng
- Nếu dùng Gmail, tạo App Password (không dùng password tài khoản bình thường)
- Kiểm tra `SMTP_USE_TLS` / `SMTP_USE_SSL` đúng với port

### Lỗi Gemini API

```
Error: Invalid API key
```

**Giải pháp:**
- Xác nhận `GEMINI_API_KEY` đúng từ https://aistudio.google.com/api-keys
- Kiểm tra API được enable trên project GCP

### WebRTC không hoạt động

```
Peer connection failed
```

**Giải pháp:**
- Sử dụng TURN server cho NAT traversal: set `WEBRTC_ICE_SERVERS` với TURN credentials
- Mặc định chỉ dùng Google STUN (free nhưng giới hạn cho private network)

---

## Cấu Trúc Dự Án

```
.
├── agent.py                 # Main Flask + Socket.IO server
├── save_mysql.py            # Database helpers
├── send_mail.py             # Email & webhook helpers
├── config_py.py             # Startup & initialization
├── memory.py                # Advanced conversation memory
├── rag.py                   # RAG system
├── prompt.py                # AI prompts
├── struc_lesson.py          # Lesson structure normalization
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── README.md                # This file
├── .github/workflows/
│   └── python-tests.yml     # GitHub Actions CI
├── migrations/              # Database migrations
├── scripts/                 # Test scripts
│   ├── test_messages.py
│   ├── test_reports.py
│   └── test_socketio.py
├── templates/               # HTML templates
│   ├── chatbot.html
│   ├── flashcards.html      # Pagination enabled
│   ├── posts.html           # Pagination enabled
│   ├── webrtc_demo.html
│   └── ...
└── static/                  # CSS, JS assets
```

---

## Features

✅ Chatbot AI với context nhớ dài hạn (FAISS semantic search)  
✅ Phần thưởng streak + flashcards từ vựng  
✅ Cộng đồng: bài viết, bình luận, reaction  
✅ Messaging (private + group) via Socket.IO  
✅ Moderation: report, infractions, auto-ban  
✅ WebRTC voice calls (STUN/TURN configurable)  
✅ Admin dashboard & analytics  
✅ Pagination cho flashcards & posts  
✅ Structured logging & env-driven config  

---

## Support

Gặp vấn đề? Kiểm tra:
- File `.env` hợp lệ
- MySQL đang chạy
- API keys hợp lệ
- Xem logs: `LOG_LEVEL=DEBUG`

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
