# 🚀 HƯỚNG DẪN NHANH - Kết Nối Chat AI

## ⚡ 3 Bước Thiết Lập (5 phút)

### 1️⃣ Tìm IP Machine Backend
```powershell
# Mở PowerShell và chạy
ipconfig
```
Ghi nhớ dòng `IPv4 Address` (ví dụ: `192.168.1.100`)

### 2️⃣ Cập Nhật IP trong App
Mở file `app/config.js`:
```javascript
BASE_URL: 'http://192.168.1.100:5000',  // ← Thay IP của bạn
```

### 3️⃣ Chạy Backend & Frontend

**Terminal 1 - Backend (Python):**
```bash
cd c:\AI_folder\tess
python agent.py
```

**Terminal 2 - Frontend (React Native):**
```bash
cd app
npm install
npm start
```

---

## ✅ Test Kết Nối

1. Mở app → Màn hình Login
2. Nhập:
   - Email: `admin@gmail.com`
   - Password: `bao123`
3. Nhấn "Log In"
4. Vào Home → Nhấn "Chatbot với AI"
5. Gửi tin nhắn → Nên nhận phản hồi từ AI

---

## 🐛 Troubleshooting

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-----------|---------|
| "Không kết nối được" | IP sai | Kiểm tra IP bằng `ipconfig` |
| "Email/Password sai" | DB không có tài khoản | Tạo tài khoản mới via register |
| "Tin nhắn không gửi" | Server không chạy | Chạy `python agent.py` |
| "CORS Error" | Frontend khác domain | Xác nhận CORS bật trên backend |

---

## 📱 Chạy trên Android Emulator

Nếu dùng Android Emulator, thay IP:
```javascript
BASE_URL: 'http://10.0.2.2:5000',  // IP emulator mặc định
```

---

## 💡 Tips

- ✅ Luôn chạy backend trước frontend
- ✅ Backend + Frontend phải trên cùng WiFi
- ✅ Kiểm tra firewall không chặn port 5000
- ✅ Nếu lỗi DB, backup rồi xóa `aichat2.db` để tạo mới

---

**Nếu vẫn gặp lỗi, kiểm tra console của:**
- React Native (Expo DevTools)
- Python backend (terminal)
