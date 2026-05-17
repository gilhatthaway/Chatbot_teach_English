import os
import json
import re
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.sanitize import safe_invoke
from save_mysql import connect_to_mysql, get_quiz_documents_by_ids

class RAGSystem:
    def __init__(self, api_key: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        Khởi tạo hệ thống RAG với Vector Database (ChromaDB) và Embedding Model.
        """
        self.api_key = api_key
        self.embedding_model = SentenceTransformer(model_name)
        self.llm = ChatGoogleGenerativeAI(api_key=api_key, model="gemini-2.5-flash", temperature=0.7)

        # Khởi tạo ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="quiz_documents")

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Chia văn bản thành chunks với overlap.
        Chunking Strategy: Chia theo số từ với overlap để giữ ngữ cảnh.
        """
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = words[i:i + chunk_size]
            if chunk:
                chunks.append(" ".join(chunk))
        return chunks

    def add_document(self, doc_id: str, title: str, content: str):
        """
        Thêm tài liệu vào vector database.
        """
        chunks = self.chunk_text(content)
        embeddings = self.embedding_model.encode(chunks).tolist()

        # Metadata cho mỗi chunk
        metadatas = [{"doc_id": doc_id, "title": title, "chunk_index": i} for i in range(len(chunks))]
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

    def update_document(self, doc_id: str, title: str, content: str):
        """
        Cập nhật tài liệu trong vector database.
        """
        # Xóa chunks cũ
        existing_ids = self.collection.get(where={"doc_id": doc_id})["ids"]
        if existing_ids:
            self.collection.delete(ids=existing_ids)

        # Thêm lại
        self.add_document(doc_id, title, content)

    def delete_document(self, doc_id: str):
        """
        Xóa tài liệu khỏi vector database.
        """
        existing_ids = self.collection.get(where={"doc_id": doc_id})["ids"]
        if existing_ids:
            self.collection.delete(ids=existing_ids)

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy vấn vector database để lấy chunks liên quan nhất.
        """
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        relevant_chunks = []
        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            relevant_chunks.append({
                "content": doc,
                "metadata": meta,
                "similarity": 1 - dist  # Cosine similarity
            })

        return relevant_chunks

    def generate_quiz_with_rag(self, document_ids: List[int], title: str, description: str, num_questions: int = 15) -> Dict[str, Any]:
        """
        Sinh quiz sử dụng RAG: Chunking -> Embedding -> Vector DB -> Retrieval -> Generation
        """
        # Lấy tài liệu từ database
        docs = get_quiz_documents_by_ids(document_ids)
        if not docs:
            return None

        # Thêm/cập nhật tài liệu vào vector DB
        for doc in docs:
            doc_id = str(doc["id_document"])
            self.update_document(doc_id, doc["tieu_de"], doc["noi_dung"])

        # Tạo query để retrieve context
        query = f"Tạo quiz về {title} dựa trên nội dung tài liệu"
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k=10)

        # Ghép context từ chunks
        context = "\n\n".join([chunk["content"] for chunk in relevant_chunks])

        # Prompt cho LLM sinh quiz với thời gian
        prompt = f"""
Bạn là giáo viên tiếng Anh chuyên nghiệp. Dựa trên nội dung sau:

{context}

Hãy tạo một bài quiz gồm {num_questions} câu về chủ đề "{title}".
Mô tả: {description}

Yêu cầu:
- 4 câu vocabulary: sắp xếp từ, đoán từ qua ảnh (mô tả), câu đố từ ngữ, từ cấm.
- Phần còn lại: grammar & structure (trắc nghiệm, điền chỗ trống, viết lại câu).
- Với mỗi câu: type, section, question, options (nếu có), answer, explanation, hint.
- Tự động quyết định thời gian làm bài: 15, 20, hoặc 30 phút dựa trên độ khó và số câu.
- Trả về JSON duy nhất với cấu trúc:
{{
  "title": "{title}",
  "description": "{description}",
  "duration_minutes": <15|20|30>,
  "questions": [...]
}}

Không trả về văn bản ngoài JSON.
"""

        response = safe_invoke(self.llm, prompt)
        parsed = self.extract_json_from_response(response.content)

        if parsed and "questions" in parsed:
            return parsed
        return None

    def extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """
        Trích xuất JSON từ response của LLM.
        """
        cleaned = re.sub(r"```json|```", "", text).strip()
        match = re.search(r"(\{.*\})", cleaned, re.S)
        if match:
            cleaned = match.group(1)
        try:
            return json.loads(cleaned)
        except Exception:
            return None

# Instance toàn cục
rag_system = None

def init_rag_system(api_key: str):
    global rag_system
    rag_system = RAGSystem(api_key)
    return rag_system

def get_rag_system():
    return rag_system