# 🧠 Advanced Memory System - FAISS + Semantic Search

## 📌 Tính Năng Chính

### 1. **Stateful Memory**
- Lưu lịch sử hội thoại per user
- Auto-save vào disk (JSON)
- Load lịch sử khi khởi động

### 2. **FAISS Semantic Search**
- Embedding text bằng `sentence-transformers`
- Tìm kiếm ngữ cảnh liên quan (top-k)
- Tăng chất lượng response từ AI

### 3. **Auto-Summarization**
- Tóm tắt lịch sử cũ sau N tin nhắn
- Giảm token cost
- Giữ ngữ cảnh quan trọng

### 4. **Recent Context**
- Lấy 10 tin nhắn gần nhất
- Đưa vào prompt để AI hiểu context

---

## 🔧 Cấu Hình (Config)

```python
CONFIG = {
    "recent_n": 10,          # Số tin nhắn gần nhất
    "top_k": 5,              # Số kết quả semantic search
    "summarize_every": 30,   # Summarize sau N tin nhắn
    "max_history": 100       # Tối đa số tin nhắn
}
```

---

## 📖 API Endpoints

### 1. **Chat (Cải Tiến)**
```http
POST /chat
Content-Type: application/json

{
    "message": "Hello teacher",
    "id_user": 123
}
```

**Response:**
```json
{
    "response_english": "Hi! How can I help you today?",
    "explanation_vietnamese": "...",
    "correction": null
}
```

**Tội gì:**
- Tự động lấy context từ memory
- Semantic search các tin nhắn liên quan
- Gắn vào prompt để AI trả lời tốt hơn

---

### 2. **Xem Lịch Sử**
```http
GET /chat/history/<id_user>
```

**Response:**
```json
{
    "status": "success",
    "id_user": 123,
    "message_count": 15,
    "stats": {
        "total_messages": 15,
        "user_messages": 7,
        "ai_messages": 15,
        "has_summary": false
    },
    "history": [
        {
            "user": "What is a noun?",
            "ai": "A noun is a word that names...",
            "timestamp": "2025-12-12T10:30:45.123456"
        }
    ]
}
```

---

### 3. **Semantic Search**
```http
POST /chat/search/<id_user>
Content-Type: application/json

{
    "query": "grammar rules",
    "top_k": 5
}
```

**Response:**
```json
{
    "status": "success",
    "query": "grammar rules",
    "context": "🔗 Ngữ cảnh liên quan:\nBạn: What are the rules...\nTôi: Grammar rules are...",
    "top_k": 5
}
```

---

### 4. **Xóa Lịch Sử**
```http
POST /chat/clear/<id_user>
```

**Response:**
```json
{
    "status": "success",
    "message": "Đã xóa lịch sử hội thoại của user 123"
}
```

---

## 💾 File Structure

```
memory_data/
├── history_123.json          # Lịch sử user 123
├── history_456.json          # Lịch sử user 456
└── ...
```

**Cấu trúc JSON:**
```json
[
    {
        "user": "Hello",
        "ai": "Hi there!",
        "timestamp": "2025-12-12T10:30:45.123456",
        "embedding": [0.1, 0.2, ..., 0.384]
    }
]
```

---

## 🚀 Cách Hoạt Động

### **Flow Khi Chat:**

```
1. User gửi message
   ↓
2. Load lịch sử từ memory
   ↓
3. Lấy 10 tin nhắn gần nhất (recent context)
   ↓
4. Embed message + semantic search (top 5 liên quan)
   ↓
5. Gắn cả recent + semantic vào prompt
   ↓
6. Gửi tới Gemini API
   ↓
7. Embed response + thêm vào FAISS index
   ↓
8. Save lịch sử vào disk
   ↓
9. Trả về response cho user
   ↓
10. Auto-summarize nếu > 30 tin nhắn
```

---

## ⚙️ Configuration Tuning

### **Để Response Tốt Hơn:**
```python
CONFIG = {
    "recent_n": 15,       # Tăng để giữ nhiều context
    "top_k": 8,           # Tăng kết quả semantic search
    "max_history": 200    # Tăng lưu lịch sử
}
```

### **Để Tiết Kiệm Token:**
```python
CONFIG = {
    "recent_n": 5,        # Giảm để tiết kiệm
    "top_k": 3,           # Tìm ít kết quả hơn
    "summarize_every": 15 # Summarize sớm hơn
}
```

---

## 📊 Model Embedding

**Hiện dùng:**
- Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Dimension: 384
- Hỗ trợ: 100+ ngôn ngữ

**Thay đổi model:**
```python
# memory.py
embedding_model = SentenceTransformer("model-name")
emb_dim = embedding_model.get_sentence_embedding_dimension()
```

---

## 🔍 Debug

### **Xem embedding:**
```python
from memory import embedding_model
text = "Hello world"
emb = embedding_model.encode(text)
print(emb)  # Vector 384 chiều
```

### **Xem FAISS index:**
```python
from memory import conversation_memory
user_id = 123
index = conversation_memory.faiss_indexes[user_id]
print(f"Total vectors: {index.ntotal}")
```

---

## 🎯 Best Practices

1. **Định kỳ xóa lịch sử cũ:**
   - Gọi `POST /chat/clear/<id_user>` mỗi tháng
   - Hoặc thiết lập `max_history` hợp lý

2. **Monitor memory usage:**
   - Mỗi embedding = 384 * 4 bytes ≈ 1.5 KB
   - 100 tin nhắn ≈ 150 KB per user

3. **Test semantic search:**
   - Dùng API `/chat/search` để verify quality
   - Adjust `top_k` nếu cần

---

## ❓ FAQ

**Q: Giữ nhiều context hay ít context?**
A: Nhiều context = response tốt hơn nhưng token nhiều. Cân bằng tại `recent_n=10, top_k=5`

**Q: Summarization có mất info không?**
A: Có, nhưng giữ lại info quan trọng. Bạn có thể tắt bằng `summarize_every=999`

**Q: Embedding model nào tốt nhất?**
A: `paraphrase-multilingual-MiniLM-L12-v2` cân bằng tốc độ + chất lượng. Nếu cần chính xác cao dùng `bert-base-multilingual-uncased`

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

**Các package mới:**
- `faiss-cpu` - Vector search
- `sentence-transformers` - Text embedding
- `numpy` - Array operations
