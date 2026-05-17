from langchain_google_genai import ChatGoogleGenerativeAI
from prompt import BASE_ROLE_PROMPT, PROMPTS, CHATBOT_PROMPT, VOICE_PROMPT
from dotenv import load_dotenv
from flask import Flask, render_template, send_file, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import json
import logging
import sys
import time
import shutil
from struc_lesson import *
import re
from save_mysql import *
import speech_recognition as sr
from gtts import gTTS
import sounddevice as sd
import scipy.io.wavfile as wav
import pygame
from config_py import startup
from send_mail import send_otp, send_flashcard_email, send_admin_notification, send_admin_webhook
import random
from memory import conversation_memory
from rag import init_rag_system, get_rag_system
from utils.sanitize import safe_invoke
from datetime import datetime
load_dotenv()

# Setup structured logging early
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('agent')

import builtins

_old_print = builtins.print

def _print_to_logger(*args, **kwargs):
    try:
        msg = ' '.join(str(a) for a in args)
        if '❌' in msg or 'Lỗi' in msg or 'Error' in msg:
            logger.error(msg)
        elif '⚠️' in msg or 'Warning' in msg:
            logger.warning(msg)
        else:
            logger.info(msg)
    except Exception:
        _old_print(*args, **kwargs)

builtins.print = _print_to_logger

def validate_required_env():
    missing = []
    required = ['SMTP_EMAIL', 'SMTP_PASS']
    for k in required:
        if not os.getenv(k):
            missing.append(k)
    if missing:
        logger.warning('Missing recommended environment variables: %s', ','.join(missing))

validate_required_env()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class EnglishTeachingAgent:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model=model,
            temperature=1
        )

    def generate(self, task: str, **kwargs) -> dict:
        if task not in PROMPTS:
            raise ValueError(f"Nhiệm vụ {task} chưa được định nghĩa trong PROMPTS")

        full_prompt = BASE_ROLE_PROMPT + "\n\n" + PROMPTS[task].format(**kwargs)
        response = safe_invoke(self.llm, full_prompt)

        try:
            result_json = json.loads(response.content)
        except json.JSONDecodeError:
            result_json = {"content": response.content}

        return result_json

API_KEY = "AIzaSyD9IEfIvxClIqy3Sf3VbwomiI_-mQye6Wo"
agent = EnglishTeachingAgent(api_key=API_KEY)
rag_system = init_rag_system(API_KEY)

# Trang đăng nhập
@app.route('/')
def index():
    return render_template("login.html")

# Trang chủ
@app.route('/home')
def index_page():
    return render_template("index.html")

# Trang Profile cá nhân
@app.route("/profile")
def profile_page():
    return render_template("profile.html")

# Trang Đổi mật khẩu
@app.route("/change_password")
def change_password_page():
    return render_template("change_password.html")

# Trang voice
@app.route('/voice')
def voice_page():
    return render_template("voice.html")

# Trang bài học
@app.route('/lesson')
def lesson_page():
    return render_template("lesson.html")

# Trang AI chatbot
@app.route('/chatbot')
def chatbot_page():
    return render_template("chatbot.html")

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/ad_streak')
def ad_streak():
    return render_template('ad_streak.html')

@app.route('/api/admin/streaks/all', methods=['GET'])
def api_admin_get_all_streaks():
    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_nguoi_dung, ten_dang_nhap, email, streak_count, last_streak_date FROM nguoi_dung ORDER BY streak_count DESC"
        )
        users = cursor.fetchall() or []
        return jsonify({"status": "success", "users": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/leaderboard/reward_top', methods=['POST'])
def api_leaderboard_reward_top():
    results = reward_top_streak_users(limit=10)
    return jsonify({"status": "success", "results": results})

@app.route('/api/leaderboard/top', methods=['GET'])
def api_leaderboard_top():
    top = get_top_streak_users(limit=10)
    return jsonify({"status": "success", "top": top})

@app.route('/api/admin/streak/<int:id_nguoi_dung>', methods=['PUT'])
def api_admin_update_streak(id_nguoi_dung):
    data = request.get_json() or {}
    new_streak = data.get('streak_count')
    
    if new_streak is None or not isinstance(new_streak, int):
        return jsonify({"status": "error", "message": "streak_count phải là số"}), 400
    
    success = update_user_streak_by_admin(id_nguoi_dung, new_streak)
    return jsonify({
        "status": "success" if success else "error",
        "message": "Được cập nhật" if success else "Cập nhật thất bại"
    })

@app.route('/api/admin/streak/<int:id_nguoi_dung>/reset', methods=['POST'])
def api_admin_reset_streak(id_nguoi_dung):
    success = reset_user_streak(id_nguoi_dung)
    return jsonify({
        "status": "success" if success else "error",
        "message": "Streak được reset" if success else "Reset thất bại"
    })

@app.route('/api/admin/rewards/all', methods=['GET'])
def api_admin_get_all_rewards():
    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id_reward, r.id_nguoi_dung, u.ten_dang_nhap, r.tu_vung, r.y_nghia, r.ly_do, r.issued_at "
            "FROM flashcard_rewards r "
            "JOIN nguoi_dung u ON r.id_nguoi_dung = u.id_nguoi_dung "
            "ORDER BY r.issued_at DESC"
        )
        rewards = cursor.fetchall() or []
        return jsonify({"status": "success", "rewards": rewards})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/reward/<int:id_reward>', methods=['DELETE'])
def api_admin_delete_reward(id_reward):
    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM flashcard_rewards WHERE id_reward = %s", (id_reward,))
        connection.commit()
        return jsonify({"status": "success", "message": "Flashcard được xoá"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/admin/reward/add', methods=['POST'])
def api_admin_add_reward():
    data = request.get_json() or {}
    id_nguoi_dung = data.get('id_nguoi_dung')
    tu_vung = data.get('tu_vung')
    y_nghia = data.get('y_nghia')
    ly_do = data.get('ly_do', 'Admin manual')
    
    if not id_nguoi_dung or not tu_vung or not y_nghia:
        return jsonify({"status": "error", "message": "Thiếu thông tin"}), 400
    
    success = insert_flashcard_reward(id_nguoi_dung, tu_vung, y_nghia, ly_do)
    return jsonify({
        "status": "success" if success else "error",
        "message": "Flashcard được thêm" if success else "Thêm thất bại"
    })


# Admin dashboard page
@app.route('/admin/dashboard')
def admin_dashboard_page():
    return render_template('admin_dashboard.html')


# Simple persistent notification settings stored in repository JSON file
NOTIFICATION_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'notification_settings.json')


def read_notification_settings():
    try:
        if os.path.exists(NOTIFICATION_SETTINGS_PATH):
            with open(NOTIFICATION_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"admin_email": os.getenv('ADMIN_NOTIFICATION_EMAIL', ''), "admin_webhook": os.getenv('ADMIN_NOTIFICATION_WEBHOOK', '')}


def write_notification_settings(data: dict):
    try:
        with open(NOTIFICATION_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print('Error writing notification settings:', e)
        return False


@app.route('/admin/notifications', methods=['GET', 'POST'])
def admin_notifications():
    if request.method == 'POST':
        admin_email = (request.form.get('admin_email') or '').strip()
        admin_webhook = (request.form.get('admin_webhook') or '').strip()
        write_notification_settings({"admin_email": admin_email, "admin_webhook": admin_webhook})
        return redirect(url_for('admin_notifications'))

    settings = read_notification_settings()
    return render_template('admin_notifications.html', settings=settings)


@app.get('/api/admin/users/summary')
def api_admin_users_summary():
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor(dictionary=True)
        # total users
        cursor.execute("SELECT COUNT(*) AS total FROM nguoi_dung")
        total_users = cursor.fetchone().get('total', 0)
        # total lessons
        cursor.execute("SELECT COUNT(*) AS total FROM baihoc")
        total_lessons = cursor.fetchone().get('total', 0)
        # total AI chats
        cursor.execute("SELECT COUNT(*) AS total FROM AI_chat")
        total_chats = cursor.fetchone().get('total', 0)
        # total AI voices
        cursor.execute("SELECT COUNT(*) AS total FROM AI_voice")
        total_voices = cursor.fetchone().get('total', 0)

        # sample users list (limit 200)
        cursor.execute("SELECT id_nguoi_dung, ten_dang_nhap, email, vai_tro FROM nguoi_dung ORDER BY id_nguoi_dung DESC LIMIT 200")
        users = cursor.fetchall() or []

        return jsonify({
            "status": "success",
            "summary": {
                "total_users": total_users,
                "total_lessons": total_lessons,
                "total_chats": total_chats,
                "total_voices": total_voices
            },
            "users": users
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try:
            if conn.is_connected():
                cursor.close(); conn.close()
        except:
            pass


@app.get('/api/admin/user_planner/<int:id_nguoi_dung>')
def api_admin_get_user_planner(id_nguoi_dung):
    try:
        data = get_user_planner(id_nguoi_dung)
        if not data:
            return jsonify({"status": "error", "message": "No planner found"}), 404
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.post('/api/admin/user_planner/<int:id_nguoi_dung>')
def api_admin_save_user_planner(id_nguoi_dung):
    try:
        data = request.get_json() or {}
        planner = data.get('planner', None)
        # allow null to clear
        success = save_user_planner(id_nguoi_dung, planner)
        return jsonify({"status": "success" if success else "error", "message": "Saved" if success else "Failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def extract_json_from_text(text):
    if not isinstance(text, str):
        return None
    cleaned = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"(\{.*\})", cleaned, re.S)
    if match:
        cleaned = match.group(1)
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def generate_quiz_from_documents(source_documents, tieu_de, mo_ta, so_cau=15):
    """
    Sinh quiz từ tài liệu admin với thời gian tự động quyết định.
    """
    if not source_documents:
        return None
    source_lines = []
    for doc in source_documents:
        title = doc.get("tieu_de", "Tài liệu")
        content = (doc.get("noi_dung") or "")[:1200]
        source_lines.append(f"{title}: {content}")

    prompt = f"""
Bạn là một giáo viên tiếng Anh giàu kinh nghiệm, giúp học sinh ôn luyện từ vựng và ngữ pháp.
Dựa trên các tài liệu tham khảo sau đây:
{chr(10).join(source_lines)}

Hãy tạo một bài quiz gồm {so_cau} câu:
- 4 câu vocabulary: sắp xếp từ, đoán từ qua ảnh (mô tả bằng chữ), câu đố từ ngữ, từ cấm.
- Phần còn lại: grammar & structure (trắc nghiệm, điền chỗ trống, viết lại câu).
- Tự động quyết định thời gian làm bài: 15, 20, hoặc 30 phút dựa trên độ khó và số câu.

Với mỗi câu, trả về JSON object có các trường:
- type: one of "word_sort", "image_guess", "word_puzzle", "banned_word", "multiple_choice", "fill_blank", "rewrite_sentence"
- section: "vocabulary" or "grammar"
- question: nội dung câu hỏi bằng tiếng Việt hoặc tiếng Anh ngắn gọn
- options: danh sách lựa chọn nếu có, hoặc []
- answer: đáp án đúng (string hoặc danh sách giá trị đúng)
- explanation: giải thích ngắn gọn
- hint: gợi ý nếu có, hoặc ""

Trả về duy nhất một JSON với cấu trúc:
{{
  "title": "{tieu_de}",
  "description": "{mo_ta}",
  "duration_minutes": <15|20|30>,
  "questions": [ ... ]
}}

Không trả về văn bản ngoài JSON.
"""

    result = safe_invoke(agent.llm, prompt)
    if not result or not hasattr(result, "content"):
        return None

    parsed = extract_json_from_text(result.content)
    if not parsed or not isinstance(parsed, dict):
        return None

    questions = parsed.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        return None

    duration_minutes = parsed.get("duration_minutes", 20)
    if duration_minutes not in [15, 20, 30]:
        duration_minutes = 20

    return create_quiz_from_questions(tieu_de, mo_ta, [doc.get("id_document") for doc in source_documents], questions, duration_minutes)


@app.route('/api/admin/quiz/document/add', methods=['POST'])
def api_admin_add_quiz_document():
    data = request.get_json() or {}
    title = (data.get("tieu_de") or "").strip()
    content = (data.get("noi_dung") or "").strip()
    if not title or not content:
        return jsonify({"status": "error", "message": "Thiếu tiêu đề hoặc nội dung tài liệu"}), 400

    doc_id = insert_quiz_document(title, content)
    if not doc_id:
        return jsonify({"status": "error", "message": "Không thêm được tài liệu"}), 500

    return jsonify({"status": "success", "id_document": doc_id})


@app.route('/api/admin/documents/all', methods=['GET'])
def api_admin_get_quiz_documents():
    docs = get_quiz_documents(100)
    return jsonify({"status": "success", "documents": docs})


@app.route('/api/admin/quizzes/all', methods=['GET'])
def api_admin_get_quizzes():
    quizzes = get_quiz_list()
    return jsonify({"status": "success", "quizzes": quizzes})


@app.route('/api/admin/quiz/generate', methods=['POST'])
def api_admin_generate_quiz():
    data = request.get_json() or {}
    title = (data.get("tieu_de") or "Quiz học tiếng Anh").strip()
    mo_ta = (data.get("mo_ta") or "Quiz tự động sinh từ tài liệu admin").strip()
    ids = data.get("document_ids") or []
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({"status": "error", "message": "Thiếu document_ids"}), 400

    docs = [get_quiz_document(int(doc_id)) for doc_id in ids if str(doc_id).isdigit()]
    docs = [d for d in docs if d]
    if not docs:
        return jsonify({"status": "error", "message": "Không tìm thấy tài liệu"}), 404

    rag = get_rag_system()
    if rag is None:
        rag = init_rag_system(API_KEY)

    quiz_data = rag.generate_quiz_with_rag(ids, title, mo_ta, num_questions=15)
    if not quiz_data:
        return jsonify({"status": "error", "message": "Không tạo được quiz từ AI"}), 500

    questions = quiz_data.get("questions")
    duration_minutes = quiz_data.get("duration_minutes", 20)
    if not isinstance(questions, list) or len(questions) == 0:
        return jsonify({"status": "error", "message": "AI trả về dữ liệu quiz không hợp lệ"}), 500

    quiz_id = create_quiz_from_questions(title, mo_ta, [doc.get("id_document") for doc in docs], questions, duration_minutes)
    if not quiz_id:
        return jsonify({"status": "error", "message": "Không lưu được quiz"}), 500

    return jsonify({"status": "success", "id_quiz": quiz_id})


@app.route('/api/admin/quiz/<int:id_quiz>/delete', methods=['DELETE'])
def api_admin_delete_quiz(id_quiz):
    success = delete_quiz(id_quiz)
    return jsonify({"status": success and "success" or "error", "message": success and "Xóa quiz thành công" or "Không xóa được quiz"})


@app.route('/api/admin/document/<int:id_document>/delete', methods=['DELETE'])
def api_admin_delete_quiz_document(id_document):
    success = delete_quiz_document(id_document)
    return jsonify({"status": success and "success" or "error", "message": success and "Xóa tài liệu thành công" or "Không xóa được tài liệu"})


@app.get('/quizzes/list')
def api_quiz_list():
    quizzes = get_quiz_list()
    return jsonify({"status": "success", "quizzes": quizzes})


@app.get('/quiz/<int:id_quiz>')
def api_get_quiz_detail(id_quiz):
    quiz = get_quiz_detail(id_quiz)
    if not quiz:
        return jsonify({"status": "error", "message": "Không tìm thấy quiz"}), 404
    return jsonify({"status": "success", "quiz": quiz})


@app.post('/quiz/submit')
def api_submit_quiz():
    data = request.get_json() or {}
    id_nguoi_dung = data.get("id_nguoi_dung")
    id_quiz = data.get("id_quiz")
    bai_lam = data.get("bai_lam", [])

    if not id_nguoi_dung or not id_quiz:
        return jsonify({"status": "error", "message": "Thiếu id_nguoi_dung hoặc id_quiz"}), 400

    result = submit_quiz(id_nguoi_dung, id_quiz, bai_lam)
    if not result:
        return jsonify({"status": "error", "message": "Lỗi khi nộp quiz"}), 500

    return jsonify({"status": "success", "result": result})


@app.get('/quiz/history/<int:id_nguoi_dung>')
def api_get_quiz_history(id_nguoi_dung):
    history = get_quiz_history(id_nguoi_dung, limit=10)
    return jsonify({"status": "success", "history": history})


# Trang lịch sử tạo bài học
@app.route("/history_page")
def history_page():
    return render_template("history.html")

@app.route('/study_planner', strict_slashes=False)
def study_planner_page():
    return render_template("study_planner.html")

@app.get('/api/user/ai_chat_history/<int:id_nguoi_dung>')
def api_user_ai_chat_history(id_nguoi_dung):
    history = get_ai_chat_history(id_nguoi_dung, limit=50)
    return jsonify({"status": "success", "history": history})

@app.get('/api/user/ai_voice_history/<int:id_nguoi_dung>')
def api_user_ai_voice_history(id_nguoi_dung):
    history = get_ai_voice_history(id_nguoi_dung, limit=50)
    for item in history:
        if item.get('audio_file'):
            item['audio_url'] = url_for('static', filename=f'audio/{item["audio_file"]}')
        else:
            item['audio_url'] = None
    return jsonify({"status": "success", "history": history})


@app.post('/api/user/ai_chat_history/<int:id_nguoi_dung>')
def api_user_save_ai_chat_history(id_nguoi_dung):
    try:
        data = request.get_json() or {}
        entries = data.get('history') or data.get('entries') or []
        success = save_ai_chat_history(id_nguoi_dung, entries)
        return jsonify({"status": "success" if success else "error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.delete('/api/user/ai_chat_history/<int:id_nguoi_dung>')
def api_user_delete_ai_chat_history(id_nguoi_dung):
    try:
        success = delete_ai_chat_history(id_nguoi_dung)
        return jsonify({"status": "success" if success else "error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.post('/api/user/ai_voice_history/<int:id_nguoi_dung>')
def api_user_save_ai_voice_history(id_nguoi_dung):
    try:
        data = request.get_json() or {}
        entries = data.get('history') or data.get('entries') or []
        success = save_ai_voice_history(id_nguoi_dung, entries)
        return jsonify({"status": "success" if success else "error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.delete('/api/user/ai_voice_history/<int:id_nguoi_dung>')
def api_user_delete_ai_voice_history(id_nguoi_dung):
    try:
        success = delete_ai_voice_history(id_nguoi_dung)
        return jsonify({"status": "success" if success else "error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/admin/exam/upload_material', methods=['POST'])
def api_admin_upload_exam_material():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Missing file"}), 400
        f = request.files['file']
        title = (request.form.get('tieu_de') or f.filename or 'uploaded_doc')[:255]
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        save_path = os.path.join(uploads_dir, f.filename)
        f.save(save_path)

        # If text-like, try to read content and store in quiz_documents for RAG ingestion
        content = None
        try:
            if f.mimetype and f.mimetype.startswith('text') or f.filename.lower().endswith(('.txt', '.md', '.json', '.csv')):
                with open(save_path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
        except Exception:
            content = None

        if content:
            doc_id = insert_quiz_document(title, content)
            return jsonify({"status": "success", "id_document": doc_id, "saved_file": save_path})
        else:
            # Store placeholder document linking to file path
            doc_id = insert_quiz_document(title, f"Uploaded file saved at: {save_path}")
            return jsonify({"status": "success", "id_document": doc_id, "saved_file": save_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.get('/api/user/notifications/<int:id_nguoi_dung>')
def api_user_notifications(id_nguoi_dung):
    try:
        docs = get_quiz_documents(5)
        lesson_count = count_user_lessons(id_nguoi_dung)
        chat_count = count_ai_chat_history(id_nguoi_dung)
        voice_count = count_ai_voice_history(id_nguoi_dung)

        notifications = []
        if docs:
            notifications.append({
                "title": "Tài liệu mới",
                "message": f"Có {len(docs)} tài liệu mới từ admin. Xem ngay để ôn luyện.",
                "type": "document"
            })
        if lesson_count > 0:
            notifications.append({
                "title": "Bài học AI",
                "message": f"Bạn đã tạo {lesson_count} bài học. Xem lại hoặc tiếp tục học nhé.",
                "type": "lesson"
            })
        if chat_count > 0:
            notifications.append({
                "title": "Chatbot AI",
                "message": f"Bạn có {chat_count} lần chat với AI. Xem lịch sử để ôn lại nội dung.",
                "type": "chat"
            })
        if voice_count > 0:
            notifications.append({
                "title": "Trợ lý giọng nói",
                "message": f"Bạn có {voice_count} phiên thoại với AI. Kiểm tra lại để cải thiện phát âm.",
                "type": "voice"
            })

        streak_info = get_user_streak_info(id_nguoi_dung)
        streak_count = streak_info["streak_count"] if streak_info else 0
        streak_points = streak_info["streak_points"] if streak_info else 0
        if streak_points > 0:
            notifications.append({
                "title": "Điểm streak",
                "message": f"Bạn có {streak_points} điểm streak. Hoàn thành 100 điểm để nhận flashcard ngẫu nhiên.",
                "type": "streak_points"
            })
        if streak_count > 0:
            notifications.append({
                "title": "Chuỗi streak ngày",
                "message": f"Bạn đang giữ streak {streak_count} ngày. Giữ vững nhé!",
                "type": "streak"
            })

        # Kiểm tra flashcard rewards gần đây và thêm thông báo nếu có
        try:
            recent_rewards = get_user_flashcard_rewards(id_nguoi_dung, limit=5)
            if recent_rewards:
                # only notify about rewards issued in the last 48 hours
                now = datetime.now()
                recent_new = [r for r in recent_rewards if isinstance(r.get('issued_at'), datetime) and (now - r.get('issued_at')).total_seconds() <= 48 * 3600]
                if recent_new:
                    notifications.append({
                        "title": "🎉 Bạn nhận được Flashcards",
                        "message": f"Bạn vừa nhận {len(recent_new)} flashcard mới. Xem chúng tại trang Flashcards.",
                        "type": "flashcard"
                    })
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "notifications": notifications,
            "recent_documents": docs,
            "counts": {
                "lessons": lesson_count,
                "chat": chat_count,
                "voice": voice_count,
                "streak_days": streak_count,
                "streak_points": streak_points,
                "documents": len(docs)
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.get("/exams/list")
def exams_list_api():
    exams = get_exams_list()
    return jsonify({"exams": exams})

#//////////////////////////// ADMIN ////////////////////////////////////////////////////
@app.route('/ad_user')
def ad_user():
    return render_template("ad_user.html")

@app.route('/ad_lesson')
def ad_lesson():
    return render_template("ad_lesson.html")

@app.route('/ad_query')
def ad_query():
    return render_template("ad_query.html")

# Trang bài kiểm tra
@app.route('/exam')
def exam_page():
    return redirect('/exam/take')


@app.route('/exam/create')
def exam_create_page():
    return render_template("exam_create.html")


@app.route('/quiz/take')
def quiz_take_page():
    return render_template("quiz_take.html")


@app.route('/ad_quiz')
def ad_quiz():
    return render_template("quiz_admin.html")


@app.route('/exam/take')
def exam_take_page():
    return render_template("exam_take.html")

#//////////////////////////////// AI CHATBOT ////////////////////////////////////////////////////
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    student_input = data.get("message", "")
    id_nguoi_dung = data.get("id_nguoi_dung")

    if not id_nguoi_dung or not student_input:
        return jsonify({"error": "Thiếu id_nguoi_dung hoặc message"}), 400

    # ✅ Lấy ngữ cảnh thông minh từ Memory (recent + semantic)
    try:
        full_context = conversation_memory.get_full_context(id_nguoi_dung, student_input)
    except Exception as e:
        logger.warning("⚠️ Lỗi lấy context từ memory: %s", e)
        # Fallback: lấy từ database
        history = get_lich_su_chat(id_nguoi_dung, limit=5)
        full_context = ""
        for role, msg in history:
            if role == "user":
                full_context += f"Người học: {msg}\n"
            else:
                full_context += f"AI: {msg}\n"

    # ✅ Tạo prompt gửi AI với ngữ cảnh đầy đủ
    chat_prompt = f"""
{CHATBOT_PROMPT}

{full_context}

Người học nói: {student_input}
"""

    # ✅ Gọi AI
    response = safe_invoke(agent.llm, chat_prompt)
    raw = response.content.strip()

    # ✅ Xóa ```json ``` nếu có
    cleaned = re.sub(r"```json|```", "", raw).strip()

    # ✅ Parse JSON nếu đúng format
    try:
        parsed = json.loads(cleaned)
    except:
        parsed = {
            "response_english": raw,
            "explanation_vietnamese": "",
            "correction": ""
        }

    # ✅ Chuẩn hóa kết quả trả về frontend
    result = {
        "response_english": parsed.get("response_english", ""),
        "explanation_vietnamese": parsed.get("explanation_vietnamese", ""),
        "correction": parsed.get("correction", "")
    }

    # ✅ Nội dung AI trả về
    noi_dung_ai = result["response_english"] + "\n" + result["explanation_vietnamese"]

    # ✅ Lưu vào Memory để sử dụng ngữ cảnh thông minh lần sau
    try:
        conversation_memory.add_message(id_nguoi_dung, student_input, noi_dung_ai)
        logger.info("✅ Lưu tin nhắn vào Memory cho user %s", id_nguoi_dung)
    except Exception as e:
        logger.warning("⚠️ Lỗi lưu vào Memory: %s", e)

    return jsonify(result)



#/////////////////////////// ĐĂNG KÝ - OTP /////////////////////////
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    ten_dang_nhap = data.get("ten_dang_nhap")
    email = data.get("email")
    mat_khau = data.get("mat_khau")

    if not ten_dang_nhap or not email or not mat_khau:
        return jsonify({"status": "error", "message": "Thiếu thông tin đăng ký!"}), 400

    conn = connect_to_mysql()
    cursor = conn.cursor()

# kiểm tra email đã tồn tại trong bảng nguoi_dung chưa
    cursor.execute("SELECT id_nguoi_dung  FROM nguoi_dung WHERE email = %s", (email,))
    if cursor.fetchone():
        return jsonify({"status": "error", "message": "Email đã tồn tại!"}), 400
 # tạo OTP
    otp = str(random.randint(100000, 999999))

 # lưu thông tin + OTP vào bảng OTP_dang_ky_email
    cursor.execute("""
        INSERT INTO OTP_dang_ky_email (email, ten_dang_nhap, mat_khau, ma_otp)
        VALUES (%s, %s, %s, %s)
    """, (email, ten_dang_nhap, mat_khau, otp))
    conn.commit()

# gửi OTP
    send_otp(email, otp)

    return jsonify({
        "status": "success",
        "message": "Đã gửi mã OTP đến email của bạn!"
    }), 200



# API xác thực OTP đăng kí
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)

 # kiểm tra OTP
    cursor.execute("""
        SELECT * FROM OTP_dang_ky_email
        WHERE email = %s AND ma_otp = %s
        ORDER BY id DESC LIMIT 1
    """, (email, otp))
    
    row = cursor.fetchone()

    if not row:
        return jsonify({"status": "error", "message": "Mã OTP không đúng!"}), 400

 # lấy dữ liệu tạm
    ten_dang_nhap = row["ten_dang_nhap"]
    mat_khau = row["mat_khau"]
    
 # tạo user thật
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO nguoi_dung (ten_dang_nhap, email, mat_khau, vai_tro)
        VALUES (%s, %s, %s, 'user')
    """, (ten_dang_nhap, email, mat_khau))
    conn.commit()

    return jsonify({
        "status": "success",
        "message": "Xác minh thành công!"
    }), 201



#/////////////////////////// ĐĂNG NHẬP ///////////////////////////
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    logger.info("🔥 LOGIN API HIT")

    try:
        data = request.get_json()
        email = data.get("email")
        mat_khau = data.get("mat_khau")

        if not email or not mat_khau:
            return jsonify({"status": "error", "message": "Thiếu email hoặc mật khẩu!"}), 400

        connection = connect_to_mysql()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM nguoi_dung WHERE email = %s AND mat_khau = %s", (email, mat_khau))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "error", "message": "Sai email hoặc mật khẩu!"}), 401

        return jsonify({
            "status": "success",
            "message": "Đăng nhập thành công!",
            "id_nguoi_dung": user.get("id_nguoi_dung"),
            "ten_dang_nhap": user["ten_dang_nhap"],
            "vai_tro": user["vai_tro"]
        }), 200

    except Exception as e:
        logger.exception("❌ ERROR: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500
# ///// ĐỔI MẬT KHẨU/////
@app.route("/change_password", methods=["PUT"])
def change_password():
    data = request.get_json()

    email = data.get("email")
    old_mat_khau = data.get("old_mat_khau")
    new_mat_khau = data.get("new_mat_khau")

    # Kiểm tra thiếu input
    if not email or not old_mat_khau or not new_mat_khau:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu!"}), 400

    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)

    # Kiểm tra mật khẩu cũ
    cursor.execute(
        "SELECT * FROM nguoi_dung WHERE email=%s AND mat_khau=%s",
        (email, old_mat_khau)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({"status": "error", "message": "Mật khẩu hiện tại không đúng!"}), 401

    # Cập nhật mật khẩu
    cursor.execute(
        "UPDATE nguoi_dung SET mat_khau=%s WHERE email=%s",
        (new_mat_khau, email)
    )
    conn.commit()

    # Đóng kết nối
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "message": "Đổi mật khẩu thành công!"}), 200




#/////////////////////////////////////////////////////////////////
#  QUÊN MẬT KHẨU – GỬI OTP
def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp(email, otp):
    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM otp_quen_mat_khau WHERE email=%s", (email,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE otp_quen_mat_khau SET otp=%s WHERE email=%s", (otp, email))
    else:
        cursor.execute("INSERT INTO otp_quen_mat_khau (email, otp) VALUES (%s, %s)", (email, otp))

    conn.commit()
    cursor.close()
    conn.close()

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT id_nguoi_dung FROM nguoi_dung WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"status": "error", "message": "Email không tồn tại!"})

    otp = generate_otp()
    save_otp(email, otp)
    send_otp(email, otp)

    return jsonify({"status": "success", "message": "Đã gửi mã OTP!"})

# ✅ API XÁC THỰC OTP QUÊN MẬT KHẨU (API MỚI)
@app.route("/verify_forgot_otp", methods=["POST"])
def verify_forgot_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)

    # Kiểm tra OTP trong bảng otp_quen_mat_khau
    cursor.execute("SELECT * FROM otp_quen_mat_khau WHERE email=%s AND otp=%s", (email, otp))
    row = cursor.fetchone()

    if row:
        return jsonify({"status": "success", "message": "OTP hợp lệ!"}), 200

    return jsonify({"status": "error", "message": "OTP không đúng!"}), 400


# 👉 THÊM ĐẶT MẬT KHẨU MỚI
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    new_mat_khau = data.get("new_mat_khau")

    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("UPDATE nguoi_dung SET mat_khau=%s WHERE email=%s", (new_mat_khau, email))
        conn.commit()
        return jsonify({"status": "success", "message": "Đổi mật khẩu thành công!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()



#/////////////////////// ADMIN /////////////////////////////////
@app.route("/update_user", methods=["PUT"])
def api_update_user():
    data = request.get_json()
    id_nguoi_dung = data.get("id_nguoi_dung") or data.get("id")
    ten_dang_nhap = data.get("ten_dang_nhap")
    email = data.get("email")
    mat_khau = data.get("mat_khau")
    vai_tro = data.get("vai_tro")

    success = update_user(id_nguoi_dung, ten_dang_nhap, email, mat_khau, vai_tro)
    message = "Cập nhật người dùng thành công" if success else "Cập nhật người dùng thất bại"
    return jsonify({"status": "success" if success else "error", "message": message})


@app.route("/delete_user/<int:id_nguoi_dung>", methods=["DELETE"])
def api_delete_user(id_nguoi_dung):
    success = delete_user(id_nguoi_dung)
    message = "Xóa người dùng thành công" if success else "Xóa người dùng thất bại"
    return jsonify({"status": "success" if success else "error", "message": message})


@app.route("/get_all/nguoi_dung", methods=["GET"])
def api_get_nguoi_dung():
    return jsonify(show_all_nguoi_dung())


@app.route("/add/nguoi_dung", methods=["POST"])
def api_add_user():
    data = request.get_json()
    ten_dang_nhap = data.get("ten_dang_nhap")
    email = data.get("email")
    mat_khau = data.get("mat_khau")
    vai_tro = data.get("vai_tro", "user")

    success, msg = admin_insert_user(ten_dang_nhap, email, mat_khau, vai_tro)
    return jsonify({"status": "success" if success else "error", "message": msg})


#//////////////// API tạo bài học///////////////////
@app.route('/generate/lesson/<topic>', methods=["POST"])
def generate_content(topic):
    try:
        # Lấy dữ liệu từ request JSON
        data = request.get_json()
        id_nguoi_dung = data.get("id_nguoi_dung")

        if not id_nguoi_dung:
            return jsonify({"error": "Thiếu id_nguoi_dung"}), 400

        # Bước 1: Tạo bài học ban đầu từ AI
        logger.info("🚀 Bước 1: Tạo bài học ban đầu cho user %s, chủ đề '%s'", id_nguoi_dung, topic)
        lesson_data = agent.generate("lesson", topic=topic)
        content = lesson_data.get('content', '{}')
        logger.debug("🔥 AI raw content: %s", content)

        # --- parse JSON từ AI ---
        try:
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                    ai_json = json.loads(json_str)
                else:
                    ai_json = {"topic": topic}
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                    ai_json = json.loads(json_str)
                else:
                    ai_json = {"topic": topic}
            else:
                ai_json = json.loads(content)
        except json.JSONDecodeError as e:
            logger.exception("❌ JSON Parse Error: %s", e)
            logger.debug("Raw content: %s", content)
            ai_json = {"topic": topic}

        # Bước 2: Chuẩn hóa cấu trúc và tạo exercises mẫu
        logger.info("🔧 Bước 2: Chuẩn hóa cấu trúc và tạo exercises")
        standardized_lesson = standardize_lesson(ai_json, topic)
        logger.debug("✅ Standardized lesson JSON: %s", json.dumps(standardized_lesson, ensure_ascii=False, indent=2))

        # Bước 3: Đưa bài học đã chuẩn hóa qua AI lần 2 để tối ưu hóa
        logger.info("🎯 Bước 3: Tối ưu hóa bài học qua AI")
        lesson_json_str = json.dumps(standardized_lesson, ensure_ascii=False, indent=2)

        final_lesson_data = agent.generate("finalize_lesson", lesson_data=lesson_json_str)
        final_content = final_lesson_data.get('content', '{}')
        logger.debug("🌟 AI final content: %s", final_content)

        try:
            if "```json" in final_content:
                start = final_content.find("```json") + 7
                end = final_content.find("```", start)
                if end != -1:
                    json_str = final_content[start:end].strip()
                    final_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No closing ``` found", final_content, 0)
            elif "```" in final_content:
                start = final_content.find("```") + 3
                end = final_content.find("```", start)
                if end != -1:
                    json_str = final_content[start:end].strip()
                    final_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No closing ``` found", final_content, 0)
            else:
                final_result = json.loads(final_content)

            logger.info("🎉 Final lesson JSON: %s", json.dumps(final_result, ensure_ascii=False, indent=2))

             # Đảm bảo dữ liệu trả về cho frontend luôn theo cấu trúc chuẩn
            final_standardized = standardize_lesson(final_result, topic)
            final_json_str = json.dumps(final_standardized, ensure_ascii=False)
            
            insert_ai_lesson(id_nguoi_dung, topic, final_json_str, "gemini 2.5")

            return jsonify(final_standardized)
    
        except json.JSONDecodeError as e:
            logger.warning("⚠️ AI không trả về JSON hợp lệ: %s", e)
            return jsonify(standardized_lesson)

    except Exception as e:
        logger.exception("❌ Error generating content: %s", e)
        return jsonify({"error": str(e)}), 500
    

# API: Lấy lịch sử học của user
@app.route("/history/lesson/<int:id_nguoi_dung>", methods=["GET"])
def get_lesson_history(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_baihoc, chu_de, model_ai, ngay_tao
            FROM baihoc
            WHERE id_nguoi_dung = %s
            ORDER BY ngay_tao DESC
        """, (id_nguoi_dung,))

        rows = cursor.fetchall()

        return jsonify({
            "status": "success",
            "history": rows
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

import ast  # ⬅ dùng để parse chuỗi dict Python
# API xem chi tiết bài học

@app.route("/history/lesson/detail/<int:id_baihoc>")
def get_lesson_detail(id_baihoc):
    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM baihoc WHERE id_baihoc=%s", (id_baihoc,))
    lesson = cursor.fetchone()

    if not lesson:
        return jsonify({"error": "Không tìm thấy bài học"})

    raw = lesson["noi_dung_baihoc"]

    # Xóa ký hiệu AI
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    # ==========================
    # 1) THỬ DECODE JSON CHUẨN
    # ==========================
    try:
        parsed = json.loads(cleaned)
        return jsonify({"lesson": parsed})
    except:
        pass  # tiếp tục xử lý phía dưới

    # ======================================================
    # 2) Nếu JSON thất bại → thử parse Python dict (AI hay trả kiểu này)
    # ======================================================
    try:
        parsed = ast.literal_eval(cleaned)
        return jsonify({"lesson": parsed})
    except:
        pass

    # ======================================================
    # 3) Nếu vẫn lỗi → cố convert " 'key': 'value' " → JSON hợp lệ
    # ======================================================
    try:
        fixed = cleaned.replace("'", '"')
        parsed = json.loads(fixed)
        return jsonify({"lesson": parsed})
    except:
        pass

    # ======================================================
    # 4) Không parse được → tr



#   API xóa bài học
@app.route("/history/lesson/delete/<int:id_baihoc>", methods=["DELETE"])
def delete_lesson(id_baihoc):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM baihoc WHERE id_baihoc = %s", (id_baihoc,))
        conn.commit()

        return jsonify({"status": "success", "message": "Đã xóa bài học!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()


#   API đếm số bài học
@app.route("/history/lesson/count/<int:id_nguoi_dung>", methods=["GET"])
def count_lesson(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM baihoc WHERE id_nguoi_dung = %s
        """, (id_nguoi_dung,))

        total = cursor.fetchone()[0]

        return jsonify({"status": "success", "total": total})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()
#  API thống kê bài học theo ngày
@app.route("/history/lesson/chart/<int:id_nguoi_dung>", methods=["GET"])
def lesson_chart(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DATE(ngay_tao) AS date, COUNT(*) AS total
            FROM baihoc
            WHERE id_nguoi_dung = %s
            GROUP BY DATE(ngay_tao)
            ORDER BY date ASC
        """, (id_nguoi_dung,))

        rows = cursor.fetchall()

        return jsonify({"status": "success", "chart": rows})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        cursor.close()
        conn.close()
# ////////////////VOICE////////////////////
# Biến trạng thái ghi âm
is_recording = False
recording = None
fs = 16000
filename = "input.wav"

# ====== 2. Text-to-Speech ======
def speak(text):
    try:
        out_file = "reply.mp3"
        tts = gTTS(text=text, lang="en")
        tts.save(out_file)
        pygame.mixer.init()
        pygame.mixer.music.load(out_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        return out_file
    except Exception as e:
        print("❌ Lỗi TTS:", e)
        return None


# ====== 3. API start/stop record ======
@app.route("/start_record", methods=["POST"])
def start_record():
    global is_recording, recording, id_nguoi_dung
    data = request.get_json()
    id_nguoi_dung = data.get("id_nguoi_dung")   # 🔹 lấy id_nguoi_dung từ frontend

    if not id_nguoi_dung:
        print("❌ Thiếu id_nguoi_dung")
        return jsonify({"status": "error", "message": "Thiếu id_nguoi_dung"}), 400

    if is_recording:
        print("❌ Đang ghi âm rồi!")
        return jsonify({"status": "error", "message": "Đang ghi âm rồi!"}), 400

    print(f"🎤 Bắt đầu ghi âm cho user {id_nguoi_dung}")
    recording = sd.rec(int(10 * fs), samplerate=fs, channels=1, dtype="int16")
    is_recording = True
    return jsonify({"status": "ok", "message": "Bắt đầu ghi âm"})

@app.route("/stop_record", methods=["POST"])
def stop_record():
    global is_recording, recording, id_nguoi_dung
    data = request.get_json()
    id_nguoi_dung = data.get("id_nguoi_dung")   # 🔹 lấy id_nguoi_dung từ frontend

    if not id_nguoi_dung:
        return jsonify({"status": "error", "message": "Thiếu id_nguoi_dung"}), 400

    if not is_recording:
        return jsonify({"status": "error", "message": "Chưa có ghi âm nào đang chạy!"}), 400

    sd.stop()
    wav.write(filename, fs, recording)
    is_recording = False

    audio_dir = os.path.join(app.static_folder, 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    audio_basename = f"voice_{id_nguoi_dung}_{int(time.time())}.wav"
    audio_path = os.path.join(audio_dir, audio_basename)
    try:
        shutil.copyfile(filename, audio_path)
        print(f"🛑 Dừng ghi âm, lưu vào {audio_path} cho user {id_nguoi_dung}")
    except Exception as e:
        print(f"❌ Lỗi lưu file âm thanh: {e}")
        audio_basename = None

    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)

    try:
        user_text = r.recognize_google(audio, language="en-US")
        print("🗣️ Bạn nói:", user_text)
    except sr.UnknownValueError:
        return jsonify({"status": "error", "message": "Không nhận diện được giọng nói"}), 400
    except sr.RequestError as e:
        return jsonify({"status": "error", "message": f"Lỗi Google SR: {e}"}), 500

    # ✅ Lấy ngữ cảnh từ Memory
    try:
        voice_context = conversation_memory.get_full_context(id_nguoi_dung, user_text)
    except Exception as e:
        print(f"⚠️ Lỗi lấy context từ memory: {e}")
        voice_context = ""

    voice_prompt = VOICE_PROMPT.replace("{student_input}", user_text)
    if voice_context:
        voice_prompt = f"{voice_context}\n\n{voice_prompt}"
    
    response = safe_invoke(agent.llm, voice_prompt)
    bot_reply = response.content
    print("🤖 Bot:", bot_reply)

    # ✅ Lưu hội thoại vào DB kèm id_nguoi_dung
    insert_ai_voice(id_nguoi_dung, user_text, bot_reply, "gemini 1.5", audio_basename)

    streak_data = award_streak_points(id_nguoi_dung, points=10)

    # ✅ Lưu vào Memory để sử dụng ngữ cảnh lần sau
    try:
        conversation_memory.add_message(id_nguoi_dung, user_text, bot_reply)
        print(f"✅ Lưu tin nhắn voice vào Memory cho user {id_nguoi_dung}")
    except Exception as e:
        print(f"⚠️ Lỗi lưu vào Memory: {e}")

    speak(bot_reply)

    response_data = {
        "status": "ok",
        "user_text": user_text,
        "bot_reply": bot_reply,
        "audio_url": audio_basename and url_for('static', filename=f'audio/{audio_basename}') or None,
        "streak": {
            "success": streak_data.get('success', False),
            "streak_points": streak_data.get('streak_points', 0),
            "reward_given": streak_data.get('reward_given', False),
            "reward": streak_data.get('reward')
        }
    }
    return jsonify(response_data)
#/////////////////////////// BÀI KIỂM TRA /////////////////////////

@app.route("/create/exams", methods=["POST"])
def api_create_exam():
    payload = request.get_json() or {}

    tieu_de = (payload.get("tieu_de") or "").strip()
    mo_ta = (payload.get("mo_ta") or "").strip()
    thoi_luong = int(payload.get("thoi_luong") or 60)
    cau_hoi_list = payload.get("cau_hoi") or []

    if not tieu_de or not isinstance(cau_hoi_list, list) or len(cau_hoi_list) == 0:
        return jsonify({"message": "Thiếu tiêu đề hoặc danh sách câu hỏi"}), 400

    new_id = create_exam_db(tieu_de, mo_ta, cau_hoi_list, thoi_luong)
    if not new_id:
        return jsonify({"message": "Không tạo được bài kiểm tra"}), 500

    return jsonify({"message": "success", "id_kt": new_id}), 200


#Lấy danh sách bài kiểm tra
@app.route('/gettall/exams/<int:id_kt>/submit', methods=['POST'])
def api_submit_exam_by_id(id_kt):
    payload = request.get_json() or {}
    id_nguoi_dung = payload.get("id_nguoi_dung")
    bai_lam = payload.get("bai_lam", [])

    if not id_nguoi_dung:
        return jsonify({"status": "error", "message": "Thiếu id_nguoi_dung"}), 400

    result = submit_exam(id_nguoi_dung, id_kt, bai_lam)
    if not result:
        return jsonify({"status": "error", "message": "Không lưu được kết quả"}), 500

    if result.get("status") == "pending":
        return jsonify({"status": "pending", "message": "Bài đã được nộp. Hệ thống sẽ chấm sau khoảng 15 phút."})

    return jsonify({"status": "success", "result": result})

def get_exams_list():
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.id_kt,
                b.tieu_de,
                b.mo_ta,
                b.thoi_luong,
                b.ngay_tao,
                COUNT(bk.id_cauhoi) AS so_cau
            FROM bai_kiem_tra b
            LEFT JOIN baiKT_cauhoi bk ON bk.id_kt = b.id_kt
            GROUP BY b.id_kt, b.tieu_de, b.mo_ta, b.thoi_luong, b.ngay_tao
            ORDER BY b.ngay_tao DESC
        """)
        rows = cursor.fetchall() or []

        # chuẩn hóa kiểu dữ liệu để JSON dễ dùng
        for r in rows:
            r["so_cau"] = int(r["so_cau"] or 0)
            if r.get("ngay_tao") is not None:
                r["ngay_tao"] = r["ngay_tao"].strftime("%Y-%m-%d %H:%M:%S")

        return rows
    except Error as e:
        print("❌ Lỗi khi lấy danh sách bài kiểm tra:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.get('/api/user/flashcards/<int:id_nguoi_dung>')
def api_user_flashcards(id_nguoi_dung):
    try:
        limit = int(request.args.get('limit') or 12)
        offset = int(request.args.get('offset') or 0)
        total = count_user_flashcard_rewards(id_nguoi_dung)
        cards = get_user_flashcard_rewards(id_nguoi_dung, limit=limit, offset=offset)
        out = []
        for c in (cards or []):
            item = dict(c)
            try:
                if isinstance(item.get('issued_at'), datetime):
                    item['issued_at'] = item['issued_at'].strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
            out.append(item)
        return jsonify({"status": "success", "flashcards": out, "total": total, "limit": limit, "offset": offset})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/flashcards')
def user_flashcards_page():
    return render_template('flashcards.html')

# Xóa bài kiểm tra
@app.delete("/delete/exams/<int:id_kt>")
def delete_exam(id_kt):
    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"message": "DB error"}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id_cauhoi FROM baiKT_cauhoi WHERE id_kt=%s", (id_kt,))
        rows = cursor.fetchall() or []
        ids = [r["id_cauhoi"] for r in rows]

        cursor.execute("DELETE FROM baiKT_cauhoi WHERE id_kt=%s", (id_kt,))
        cursor.execute("DELETE FROM bai_kiem_tra WHERE id_kt=%s", (id_kt,))

        if ids:
            fmt = ",".join(["%s"] * len(ids))
            cursor.execute(f"DELETE FROM cauhoi WHERE id_cauhoi IN ({fmt})", ids)
            # dap_an sẽ tự xóa do ON DELETE CASCADE

        connection.commit()
        return jsonify({"message": "Đã xóa bài kiểm tra"})
    except Error as e:
        print(e)
        connection.rollback()
        return jsonify({"message": "Không thể xóa"}), 500
    finally:
        cursor.close()
        connection.close()



# Cập nhật bài kiểm tra
@app.put("/update/exams/<int:id_kt>")
def update_exam(id_kt):
    data = request.get_json() or {}
    tieu_de = (data.get("tieu_de") or "").strip()
    mo_ta = (data.get("mo_ta") or "").strip()
    thoi_luong = int(data.get("thoi_luong") or 60)
    cau_hoi_list = data.get("cau_hoi") or []

    if not tieu_de or not cau_hoi_list:
        return jsonify({"message": "Thiếu tiêu đề hoặc danh sách câu hỏi"}), 400

    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"message": "DB error"}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # 1) update bài kiểm tra
        cursor.execute(
            "UPDATE bai_kiem_tra SET tieu_de=%s, mo_ta=%s, thoi_luong=%s, ngay_cap_nhat=NOW() WHERE id_kt=%s",
            (tieu_de, mo_ta, thoi_luong, id_kt)
        )

        # 2) lấy danh sách id_cauhoi cũ để xóa luôn câu hỏi + đáp án
        cursor.execute("SELECT id_cauhoi FROM baiKT_cauhoi WHERE id_kt=%s", (id_kt,))
        old = cursor.fetchall() or []
        old_ids = [r["id_cauhoi"] for r in old]

        # 3) xóa mapping
        cursor.execute("DELETE FROM baiKT_cauhoi WHERE id_kt=%s", (id_kt,))

        # 4) xóa câu hỏi cũ (dap_an sẽ ON DELETE CASCADE theo FK)
        if old_ids:
            fmt = ",".join(["%s"] * len(old_ids))
            cursor.execute(f"DELETE FROM cauhoi WHERE id_cauhoi IN ({fmt})", old_ids)

        # 5) insert lại câu hỏi + đáp án (giống create)
        cursor2 = connection.cursor()
        for q in cau_hoi_list:
            noi_dung = (q.get("noi_dung") or "").strip()
            loai = (q.get("loai_cau_hoi") or "").strip()
            muc_do = (q.get("muc_do") or "de").strip()
            phan_thi = (q.get("phan_thi") or "reading").strip().lower()
            dap_an = q.get("dap_an") or []

            if not noi_dung:
                raise ValueError("Câu hỏi thiếu nội dung")
            if loai not in ("trac_nghiem", "tu_luan"):
                raise ValueError("Loại câu hỏi không hợp lệ")
            if phan_thi not in ("listening", "reading", "writing", "speaking"):
                phan_thi = "reading"

            cursor2.execute(
                "INSERT INTO cauhoi (noi_dung, loai_cau_hoi, muc_do, phan_thi) VALUES (%s, %s, %s, %s)",
                (noi_dung, loai, muc_do, phan_thi)
            )
            id_cauhoi = cursor2.lastrowid

            cursor2.execute(
                "INSERT INTO baiKT_cauhoi (id_kt, id_cauhoi) VALUES (%s, %s)",
                (id_kt, id_cauhoi)
            )

            if loai == "trac_nghiem":
                if len(dap_an) < 2:
                    raise ValueError("Trắc nghiệm cần ít nhất 2 đáp án")

                correct_count = sum(1 for a in dap_an if bool(a.get("ketqua")))
                if correct_count != 1:
                    raise ValueError("Trắc nghiệm phải có đúng 1 đáp án đúng")

                for a in dap_an:
                    nd = (a.get("noi_dung") or "").strip()
                    if not nd:
                        raise ValueError("Có đáp án trắc nghiệm bị trống")
                    is_correct = bool(a.get("ketqua"))
                    cursor2.execute(
                        "INSERT INTO dap_an (id_cauhoi, noi_dung, ketqua) VALUES (%s, %s, %s)",
                        (id_cauhoi, nd, is_correct)
                    )
            else:
                ans = ""
                if isinstance(dap_an, list) and len(dap_an) > 0:
                    ans = (dap_an[0].get("noi_dung") or "").strip()
                if not ans:
                    raise ValueError("Tự luận phải có 1 đáp án đúng")

                cursor2.execute(
                    "INSERT INTO dap_an (id_cauhoi, noi_dung, ketqua) VALUES (%s, %s, %s)",
                    (id_cauhoi, ans, True)
                )

        connection.commit()
        return jsonify({"message": "Cập nhật thành công"})

    except Exception as e:
        print("❌ Lỗi update_exam:", e)
        connection.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()
@app.get("/exams/<int:id_kt>")
def api_get_exam_detail(id_kt):
    exam = get_exam_detail(id_kt)
    if not exam:
        return jsonify({"status": "error", "message": "Không tìm thấy bài kiểm tra"}), 404
    return jsonify({"status": "success", "exam": exam})

@app.get("/api/exams")
def api_exams_list():
    """API endpoint lấy danh sách bài kiểm tra"""
    exams = get_exams_list()
    return jsonify(exams)

@app.post("/exam/submit")
def api_submit_exam():
    """API endpoint nộp bài kiểm tra"""
    data = request.get_json()
    id_nguoi_dung = data.get("id_nguoi_dung")
    id_kt = data.get("id_kt")
    bai_lam = data.get("bai_lam", [])

    if not id_nguoi_dung or not id_kt:
        return jsonify({"status": "error", "message": "Thiếu id_nguoi_dung hoặc id_kt"}), 400

    result = submit_exam(id_nguoi_dung, id_kt, bai_lam)
    if not result:
        return jsonify({"status": "error", "message": "Lỗi khi nộp bài"}), 500

    if result.get("status") == "pending":
        return jsonify({"status": "pending", "message": "Bài đã được nộp. Hệ thống sẽ chấm sau khoảng 15 phút."})

    return jsonify({"status": "success", "diem": result.get("diem", 0), "message": "Nộp bài thành công"})

@app.get("/exam/history/<int:id_nguoi_dung>")
def api_get_exam_history(id_nguoi_dung):
    """API endpoint lấy lịch sử làm bài kiểm tra của user"""
    limit = request.args.get("limit", 10, type=int)
    
    from save_mysql import get_exam_history, grade_pending_exams
    grade_pending_exams(id_nguoi_dung)
    history = get_exam_history(id_nguoi_dung, limit=limit)
    
    return jsonify({
        "status": "success",
        "data": history,
        "message": f"Lấy {len(history)} bài kiểm tra gần đây"
    })

@app.get("/count_lessons_all")
def count_lessons_all_api():
    data = count_all_user_baihoc() or []

    # chuẩn hoá kiểu dữ liệu cho chắc (tránh Decimal/None làm FE lỗi)
    for r in data:
        r["total_baihoc"] = int(r.get("total_baihoc") or 0)
        r["id_nguoi_dung"] = int(r.get("id_nguoi_dung") or 0)

    return jsonify(data)

#///////////////////////////////////////////////////////////////////////////////
# ✅ API QUẢN LÝ MEMORY (Ngữ cảnh & Lịch sử)
#///////////////////////////////////////////////////////////////////////////////

@app.get("/memory/stats/<int:id_nguoi_dung>")
def api_memory_stats(id_nguoi_dung):
    """Lấy thống kê memory của user"""
    try:
        stats = conversation_memory.get_stats(id_nguoi_dung)
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.get("/memory/history/<int:id_nguoi_dung>")
def api_memory_history(id_nguoi_dung):
    """Lấy toàn bộ lịch sử từ memory"""
    try:
        history = conversation_memory.get_history(id_nguoi_dung)
        # Lọc bỏ embedding để giảm dung lượng response
        clean_history = [
            {
                "user": msg["user"],
                "ai": msg["ai"],
                "timestamp": msg["timestamp"]
            }
            for msg in history
        ]
        return jsonify({
            "status": "success",
            "data": clean_history
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.delete("/memory/clear/<int:id_nguoi_dung>")
def api_memory_clear(id_nguoi_dung):
    """Xóa toàn bộ memory của user"""
    try:
        conversation_memory.clear_history(id_nguoi_dung)
        return jsonify({
            "status": "success",
            "message": f"Đã xóa memory cho user {id_nguoi_dung}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

#///////////////////////////////////////////////////////////////////////////////
@app.post('/api/community/post')
def api_create_post():
    data = request.get_json() or {}
    id_nguoi_dung = data.get('id_nguoi_dung')
    content = (data.get('content') or '').strip()
    id_community = data.get('id_community')
    media = data.get('media')

    if not id_nguoi_dung or not content:
        return jsonify({'status': 'error', 'message': 'Thiếu id_nguoi_dung hoặc nội dung'}), 400

    try:
        if is_user_banned(int(id_nguoi_dung)):
            return jsonify({'status': 'error', 'message': 'User is banned'}), 403
    except Exception:
        pass

    conn = connect_to_mysql()
    cursor = conn.cursor()
    try:
        # rate limit: count posts in last 1 minute
        cursor.execute("SELECT COUNT(*) FROM posts WHERE id_nguoi_dung=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)", (id_nguoi_dung,))
        recent_posts = cursor.fetchone()[0] or 0
        if recent_posts >= 5:
            # record infraction and maybe escalate
            try:
                record_infraction(id_nguoi_dung, 'posting_rate', weight=2)
                auto_escalate_bans(id_nguoi_dung)
            except Exception:
                pass
            return jsonify({'status': 'error', 'message': 'Bạn gửi quá nhiều bài trong thời gian ngắn. Hãy chờ.'}), 429
        cursor.execute(
            "INSERT INTO posts (id_nguoi_dung, id_community, content, media) VALUES (%s, %s, %s, %s)",
            (id_nguoi_dung, id_community, content, json.dumps(media, ensure_ascii=False) if media else None)
        )
        post_id = cursor.lastrowid
        cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)",
                       (id_nguoi_dung, 10, 'post_created', 'post', post_id))
        conn.commit()
        return jsonify({'status': 'success', 'id_post': post_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/community/posts')
def api_list_posts():
    community = request.args.get('community_id')
    limit = int(request.args.get('limit') or 20)
    offset = int(request.args.get('offset') or 0)

    conn = connect_to_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        if community:
            cursor.execute("SELECT COUNT(*) AS total FROM posts WHERE id_community = %s AND is_deleted = 0", (community,))
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM posts WHERE is_deleted = 0")
        total = cursor.fetchone().get('total', 0)

        if community:
            cursor.execute("SELECT p.*, u.ten_dang_nhap FROM posts p JOIN nguoi_dung u ON p.id_nguoi_dung = u.id_nguoi_dung WHERE p.id_community = %s AND p.is_deleted = 0 ORDER BY p.created_at DESC LIMIT %s OFFSET %s", (community, limit, offset))
        else:
            cursor.execute("SELECT p.*, u.ten_dang_nhap FROM posts p JOIN nguoi_dung u ON p.id_nguoi_dung = u.id_nguoi_dung WHERE p.is_deleted = 0 ORDER BY p.created_at DESC LIMIT %s OFFSET %s", (limit, offset))
        rows = cursor.fetchall() or []
        for r in rows:
            if r.get('media'):
                try:
                    r['media'] = json.loads(r['media'])
                except Exception:
                    pass
        return jsonify({'status': 'success', 'posts': rows, 'total': total, 'limit': limit, 'offset': offset})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/community/post/<int:id_post>/reaction')
def api_post_reaction(id_post):
    data = request.get_json() or {}
    id_nguoi_dung = data.get('id_nguoi_dung')
    reaction = data.get('reaction', 'like')

    if not id_nguoi_dung:
        return jsonify({'status': 'error', 'message': 'Thiếu id_nguoi_dung'}), 400

    conn = connect_to_mysql()
    cursor = conn.cursor()
    try:
        # dedupe: if the exact reaction exists, remove it (toggle)
        cursor.execute("SELECT id_reaction, reaction_type FROM post_reactions WHERE id_post=%s AND id_nguoi_dung=%s", (id_post, id_nguoi_dung))
        existing = cursor.fetchone()
        if existing:
            existing_type = existing[1]
            if existing_type == reaction:
                # toggle off
                cursor.execute("DELETE FROM post_reactions WHERE id_reaction=%s", (existing[0],))
                conn.commit()
                return jsonify({'status':'success','action':'removed'})
            else:
                # update to new reaction_type
                cursor.execute("UPDATE post_reactions SET reaction_type=%s WHERE id_reaction=%s", (reaction, existing[0]))
                cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (id_nguoi_dung, 1, 'post_reaction_changed', 'post', id_post))
                conn.commit()
                return jsonify({'status':'success','action':'updated'})

        # otherwise insert new reaction
        cursor.execute("INSERT INTO post_reactions (id_post, id_nguoi_dung, reaction_type) VALUES (%s,%s,%s)", (id_post, id_nguoi_dung, reaction))
        cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (id_nguoi_dung, 1, 'post_reaction', 'post', id_post))
        conn.commit()
        return jsonify({'status': 'success', 'action':'added'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/stickers')
def api_list_stickers():
    conn = connect_to_mysql(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM stickers ORDER BY created_at DESC")
        rows = cur.fetchall() or []
        return jsonify({'status': 'success', 'stickers': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cur.close(); conn.close()


@app.post('/api/community/post/<int:id_post>/sticker')
def api_post_sticker(id_post):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    sticker_id = data.get('sticker_id')
    if not user_id or not sticker_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id hoặc sticker_id'}), 400
    conn = connect_to_mysql(); cur = conn.cursor()
    try:
        # record as a reaction_type using sticker id to allow dedupe
        reaction_type = f'sticker:{sticker_id}'
        cur.execute("INSERT INTO post_reactions (id_post, id_nguoi_dung, reaction_type) VALUES (%s,%s,%s)", (id_post, user_id, reaction_type))
        cur.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (user_id, 1, 'post_sticker', 'post', id_post))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cur.close(); conn.close()


@app.post('/api/community/post/<int:id_post>/comment')
def api_post_comment(id_post):
    data = request.get_json() or {}
    id_nguoi_dung = data.get('id_nguoi_dung')
    content = (data.get('content') or '').strip()
    parent_id = data.get('parent_comment_id')

    if not id_nguoi_dung or not content:
        return jsonify({'status': 'error', 'message': 'Thiếu dữ liệu'}), 400

    try:
        if is_user_banned(int(id_nguoi_dung)):
            return jsonify({'status': 'error', 'message': 'User is banned'}), 403
    except Exception:
        pass

    conn = connect_to_mysql()
    cursor = conn.cursor()
    try:
        # rate limit comments: more than 20 comments in last 10 minutes -> block
        cursor.execute("SELECT COUNT(*) FROM comments WHERE id_nguoi_dung=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)", (id_nguoi_dung,))
        recent_comments = cursor.fetchone()[0] or 0
        if recent_comments >= 20:
            try:
                record_infraction(id_nguoi_dung, 'comment_rate', weight=1)
                auto_escalate_bans(id_nguoi_dung)
            except Exception:
                pass
            return jsonify({'status': 'error', 'message': 'Bạn bình luận quá nhanh. Hãy chờ.'}), 429
        cursor.execute("INSERT INTO comments (id_post, id_nguoi_dung, parent_comment_id, content) VALUES (%s,%s,%s,%s)", (id_post, id_nguoi_dung, parent_id, content))
        comment_id = cursor.lastrowid
        cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (id_nguoi_dung, 2, 'comment_created', 'comment', comment_id))
        conn.commit()
        return jsonify({'status': 'success', 'id_comment': comment_id})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/community/post/<int:id_post>/comments')
def api_get_comments(id_post):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT c.*, u.ten_dang_nhap FROM comments c JOIN nguoi_dung u ON c.id_nguoi_dung = u.id_nguoi_dung WHERE c.id_post = %s AND c.is_deleted = 0 ORDER BY c.created_at ASC", (id_post,))
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'comments': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/report')
def api_report():
    data = request.get_json() or {}
    reporter_id = data.get('reporter_id')
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')

    if not reporter_id or not target_type or not target_id:
        return jsonify({'status': 'error', 'message': 'Thiếu dữ liệu'}), 400

    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (%s,%s,%s,%s)", (reporter_id, target_type, target_id, reason))
        conn.commit()
        # After inserting a report, check recent reports for same target and auto-record infractions
        try:
            cur2 = conn.cursor(dictionary=True)
            cur2.execute("SELECT COUNT(*) AS cnt FROM reports WHERE target_type=%s AND target_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)", (target_type, target_id))
            cnt = cur2.fetchone().get('cnt', 0)

            # determine owner user id of the target (if applicable)
            owner_id = None
            if target_type == 'user':
                owner_id = int(target_id)
            elif target_type == 'post':
                cur2.execute("SELECT id_nguoi_dung FROM posts WHERE id_post=%s", (target_id,))
                row = cur2.fetchone();
                if row: owner_id = row.get('id_nguoi_dung')
            elif target_type == 'comment':
                cur2.execute("SELECT id_nguoi_dung FROM comments WHERE id_comment=%s", (target_id,))
                row = cur2.fetchone();
                if row: owner_id = row.get('id_nguoi_dung')
            elif target_type == 'message':
                cur2.execute("SELECT sender_id FROM messages WHERE id_message=%s", (target_id,))
                row = cur2.fetchone();
                if row: owner_id = row.get('sender_id')

            # If owner found, record an infraction and escalate when thresholds met
            if owner_id:
                try:
                    record_infraction(owner_id, f'reported_{target_type}', weight=1)
                except Exception:
                    pass
                # simple auto-ban rule: >=5 reports in 24h -> 1-day ban
                if cnt >= 5:
                    try:
                        apply_ban(owner_id, level=1, days=1, reason=f'Auto-ban: {cnt} reports in 24h')
                    except Exception:
                        pass
                    # notify admin via email/webhook
                    try:
                        admin_email = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@gmail.com')
                        subject = f'Auto-ban applied: user {owner_id} ({cnt} reports)'
                        body = f'User {owner_id} received {cnt} reports in 24 hours for target {target_type} #{target_id}. An automatic ban was applied.'
                        send_admin_notification(admin_email, subject, body)
                        # send webhook if configured (Slack, Teams, etc.)
                        webhook = os.getenv('ADMIN_NOTIFICATION_WEBHOOK')
                        if webhook:
                            try:
                                send_admin_webhook(webhook, { 'text': subject + '\n' + body })
                            except Exception:
                                pass
                    except Exception:
                        pass
                else:
                    try:
                        auto_escalate_bans(owner_id)
                    except Exception:
                        pass
            try:
                cur2.close()
            except:
                pass
        except Exception:
            pass

        return jsonify({'status': 'success'})
        
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/admin/post/<int:id_post>')
def api_admin_get_post(id_post):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT p.*, u.ten_dang_nhap FROM posts p JOIN nguoi_dung u ON p.id_nguoi_dung = u.id_nguoi_dung WHERE p.id_post=%s", (id_post,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status':'error','message':'Not found'}),404
        if row.get('media'):
            try: row['media']=json.loads(row['media'])
            except: pass
        return jsonify({'status':'success','post':row})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.get('/api/admin/comment/<int:id_comment>')
def api_admin_get_comment(id_comment):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT c.*, u.ten_dang_nhap FROM comments c JOIN nguoi_dung u ON c.id_nguoi_dung = u.id_nguoi_dung WHERE c.id_comment=%s", (id_comment,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status':'error','message':'Not found'}),404
        return jsonify({'status':'success','comment':row})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.get('/api/admin/message/<int:id_message>')
def api_admin_get_message(id_message):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT m.*, u.ten_dang_nhap AS sender_name FROM messages m LEFT JOIN nguoi_dung u ON m.sender_id = u.id_nguoi_dung WHERE m.id_message=%s", (id_message,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status':'error','message':'Not found'}),404
        if row.get('attachments'):
            try: row['attachments']=json.loads(row['attachments'])
            except: pass
        return jsonify({'status':'success','message':row})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/post/<int:id_post>/delete')
def api_admin_delete_post(id_post):
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE posts SET is_deleted=1 WHERE id_post=%s", (id_post,))
        try:
            cursor.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (admin_id, 'delete_post', 'post', id_post, None))
        except Exception:
            pass
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/comment/<int:id_comment>/delete')
def api_admin_delete_comment(id_comment):
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE comments SET is_deleted=1 WHERE id_comment=%s", (id_comment,))
        try:
            cursor.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (admin_id, 'delete_comment', 'comment', id_comment, None))
        except Exception:
            pass
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/message/<int:id_message>/delete')
def api_admin_delete_message(id_message):
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE messages SET is_deleted=1 WHERE id_message=%s", (id_message,))
        try:
            cursor.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (admin_id, 'delete_message', 'message', id_message, None))
        except Exception:
            pass
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.get('/api/admin/reports')
def api_admin_get_reports():
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT r.*, u.ten_dang_nhap AS reporter_name, h.ten_dang_nhap AS handled_name FROM reports r LEFT JOIN nguoi_dung u ON r.reporter_id = u.id_nguoi_dung LEFT JOIN nguoi_dung h ON r.handled_by = h.id_nguoi_dung ORDER BY r.created_at DESC")
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'reports': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/reports/<int:id_report>/resolve')
def api_admin_resolve_report(id_report):
    data = request.get_json() or {}
    handled_by = data.get('handled_by')
    resolution = data.get('resolution') or 'Resolved'
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE reports SET status='resolved', handled_by=%s, resolution=%s, resolved_at=NOW() WHERE id_report=%s", (handled_by, resolution, id_report))
        # log admin action
        try:
            cursor.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (handled_by, 'report_resolve', 'report', id_report, resolution))
        except Exception:
            pass
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/reports/<int:id_report>/dismiss')
def api_admin_dismiss_report(id_report):
    data = request.get_json() or {}
    handled_by = data.get('handled_by')
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE reports SET status='dismissed', handled_by=%s, resolved_at=NOW() WHERE id_report=%s", (handled_by, id_report))
        try:
            cursor.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (handled_by, 'report_dismiss', 'report', id_report, 'dismissed'))
        except Exception:
            pass
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.route('/admin/moderation')
def admin_moderation_page():
    return render_template('admin_moderation.html')


@app.route('/messages')
def messages_page():
    return render_template('messages.html')


@app.route('/groups')
def groups_page():
    return render_template('groups.html')


@app.route('/communities')
def communities_page():
    return render_template('communities.html')


@app.route('/posts')
def posts_page():
    return render_template('posts.html')


@app.route('/chat/<int:other_user_id>')
def chat_with_user(other_user_id):
    return render_template('chat_view.html', other_user_id=other_user_id)


def get_webrtc_ice_servers():
    default = [{"urls": ["stun:stun.l.google.com:19302"]}]
    raw = os.getenv('WEBRTC_ICE_SERVERS', '')
    if not isinstance(raw, str) or not raw.strip():
        return json.dumps(default)

    raw = raw.strip()
    try:
        if raw.startswith('[') or raw.startswith('{'):
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                parsed = [parsed]
            if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                return json.dumps(parsed)

        urls = [item.strip() for item in re.split(r'[\n;,]+', raw) if item.strip()]
        if urls:
            return json.dumps([{"urls": urls}])

        logger.warning('WEBRTC_ICE_SERVERS value did not parse into URLs; using default STUN only.')
    except Exception as e:
        logger.warning('Invalid WEBRTC_ICE_SERVERS, falling back to default: %s', e)
    return json.dumps(default)


@app.route('/webrtc')
def webrtc_demo():
    ice_servers = get_webrtc_ice_servers()
    return render_template('webrtc_demo.html', ice_servers=ice_servers)


@app.get('/api/admin/infractions')
def api_admin_infractions():
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT i.*, u.ten_dang_nhap FROM infractions i JOIN nguoi_dung u ON i.user_id = u.id_nguoi_dung ORDER BY i.created_at DESC LIMIT 500")
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'infractions': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/admin/bans')
def api_admin_bans():
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT b.*, u.ten_dang_nhap FROM bans b JOIN nguoi_dung u ON b.user_id = u.id_nguoi_dung ORDER BY b.created_at DESC LIMIT 200")
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'bans': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/ban')
def api_admin_ban_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    level = int(data.get('level', 1))
    days = int(data.get('days', 1))
    reason = data.get('reason')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400
    ok = apply_ban(user_id, level=level, days=days, reason=reason)
    try:
        conn = connect_to_mysql(); cur = conn.cursor()
        cur.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (None, 'manual_ban', 'user', user_id, f'level={level},days={days},reason={reason}'))
        conn.commit(); cur.close(); conn.close()
    except Exception:
        pass
    return jsonify({'status': 'success' if ok else 'error'})


@app.post('/api/admin/unban')
def api_admin_unban_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE bans SET active=0 WHERE user_id=%s", (user_id,))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/admin/bulk_ban')
def api_admin_bulk_ban():
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    user_ids = data.get('user_ids') or []
    level = int(data.get('level', 1))
    reason = data.get('reason') or 'Bulk ban'
    if not user_ids or not isinstance(user_ids, list):
        return jsonify({'status':'error','message':'Missing user_ids'}),400
    try:
        create_table_admin_actions()
    except Exception:
        pass
    conn = connect_to_mysql(); cur = conn.cursor()
    try:
        for uid in user_ids:
            try:
                apply_ban(uid, level=level, days=None, reason=reason)
                cur.execute("INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, details) VALUES (%s,%s,%s,%s,%s)", (admin_id, 'bulk_ban', 'user', uid, f'level={level},reason={reason}'))
            except Exception:
                pass
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cur.close(); conn.close()


@app.post('/api/groups/create')
def api_create_group():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = data.get('description')
    owner_id = data.get('owner_id')
    is_private = 1 if data.get('is_private') else 0

    if not name or not owner_id:
        return jsonify({'status': 'error', 'message': 'Thiếu tên hoặc owner_id'}), 400

    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO groups (name, description, is_private, owner_id) VALUES (%s,%s,%s,%s)", (name, description, is_private, owner_id))
        gid = cursor.lastrowid
        cursor.execute("INSERT INTO group_members (id_group, id_nguoi_dung, role) VALUES (%s,%s,%s)", (gid, owner_id, 'owner'))
        conn.commit()
        return jsonify({'status': 'success', 'id_group': gid})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/groups/<int:id_group>/join')
def api_join_group(id_group):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO group_members (id_group, id_nguoi_dung) VALUES (%s,%s)", (id_group, user_id))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/user/<int:target_id>/follow')
def api_user_follow(target_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status':'error','message':'Missing user_id'}),400
    try:
        create_table_follows_and_blocks()
    except Exception:
        pass
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        # toggle follow: if exists, unfollow
        cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id=%s AND followee_id=%s", (user_id, target_id))
        if cursor.fetchone()[0] > 0:
            cursor.execute("DELETE FROM follows WHERE follower_id=%s AND followee_id=%s", (user_id, target_id))
            conn.commit(); return jsonify({'status':'success','action':'unfollow'})
        cursor.execute("INSERT INTO follows (follower_id, followee_id) VALUES (%s,%s)", (user_id, target_id))
        conn.commit(); return jsonify({'status':'success','action':'follow'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.post('/api/user/<int:target_id>/block')
def api_user_block(target_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status':'error','message':'Missing user_id'}),400
    try:
        create_table_follows_and_blocks()
    except Exception:
        pass
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        # toggle block
        cursor.execute("SELECT COUNT(*) FROM blocks WHERE blocker_id=%s AND blocked_id=%s", (user_id, target_id))
        if cursor.fetchone()[0] > 0:
            cursor.execute("DELETE FROM blocks WHERE blocker_id=%s AND blocked_id=%s", (user_id, target_id))
            conn.commit(); return jsonify({'status':'success','action':'unblock'})
        cursor.execute("INSERT INTO blocks (blocker_id, blocked_id) VALUES (%s,%s)", (user_id, target_id))
        # also remove follow relationships
        cursor.execute("DELETE FROM follows WHERE follower_id=%s AND followee_id=%s", (user_id, target_id))
        cursor.execute("DELETE FROM follows WHERE follower_id=%s AND followee_id=%s", (target_id, user_id))
        conn.commit(); return jsonify({'status':'success','action':'block'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cursor.close(); conn.close()


@app.post('/api/calls/start')
def api_calls_start():
    data = request.get_json() or {}
    caller_id = data.get('caller_id')
    callee_id = data.get('callee_id')
    group_id = data.get('group_id')
    if not caller_id:
        return jsonify({'status':'error','message':'Missing caller_id'}),400
    conn = connect_to_mysql(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO calls (caller_id, callee_id, group_id, status, started_at) VALUES (%s,%s,%s,%s,NOW())", (caller_id, callee_id, group_id, 'ringing'))
        cid = cur.lastrowid
        conn.commit()
        return jsonify({'status':'success','id_call': cid})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cur.close(); conn.close()


@app.post('/api/calls/end')
def api_calls_end():
    data = request.get_json() or {}
    id_call = data.get('id_call')
    status = data.get('status', 'ended')
    recording_url = data.get('recording_url')
    if not id_call:
        return jsonify({'status':'error','message':'Missing id_call'}),400
    conn = connect_to_mysql(); cur = conn.cursor()
    try:
        cur.execute("UPDATE calls SET status=%s, ended_at=NOW(), recording_url=%s WHERE id_call=%s", (status, recording_url, id_call))
        conn.commit()
        return jsonify({'status':'success'})
    except Exception as e:
        conn.rollback(); return jsonify({'status':'error','message':str(e)}),500
    finally:
        cur.close(); conn.close()


@app.post('/api/calls/upload_recording')
def api_calls_upload_recording():
    try:
        if 'file' not in request.files:
            return jsonify({'status':'error','message':'Missing file'}),400
        f = request.files['file']
        id_call = request.form.get('id_call')
        save_dir = os.path.join(app.root_path, 'static', 'audio')
        os.makedirs(save_dir, exist_ok=True)
        filename = f"call_{int(time.time())}_{f.filename}"
        save_path = os.path.join(save_dir, filename)
        f.save(save_path)
        url = url_for('static', filename=f'audio/{filename}')
        if id_call:
            try:
                conn = connect_to_mysql(); cur = conn.cursor()
                cur.execute("UPDATE calls SET recording_url=%s, ended_at=NOW(), status='ended' WHERE id_call=%s", (url, id_call))
                conn.commit(); cur.close(); conn.close()
            except Exception:
                pass
        return jsonify({'status':'success','url': url})
    except Exception as e:
        return jsonify({'status':'error','message': str(e)}),500


@app.get('/api/calls/user/<int:user_id>')
def api_calls_for_user(user_id):
    conn = connect_to_mysql(); cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM calls WHERE caller_id=%s OR callee_id=%s ORDER BY created_at DESC", (user_id, user_id))
        rows = cur.fetchall() or []
        return jsonify({'status':'success','calls': rows})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),500
    finally:
        cur.close(); conn.close()


@app.get('/api/groups')
def api_list_groups():
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT g.*, u.ten_dang_nhap AS owner_name, COUNT(m.id_member) AS member_count FROM groups g LEFT JOIN nguoi_dung u ON g.owner_id = u.id_nguoi_dung LEFT JOIN group_members m ON g.id_group = m.id_group GROUP BY g.id_group ORDER BY g.created_at DESC")
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'groups': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/groups/<int:id_group>/members')
def api_group_members(id_group):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT gm.id_member, gm.role, u.id_nguoi_dung, u.ten_dang_nhap, u.email FROM group_members gm JOIN nguoi_dung u ON gm.id_nguoi_dung = u.id_nguoi_dung WHERE gm.id_group = %s ORDER BY gm.joined_at ASC", (id_group,))
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'members': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/communities')
def api_list_communities():
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT c.*, u.ten_dang_nhap AS owner_name FROM communities c LEFT JOIN nguoi_dung u ON c.owner_id = u.id_nguoi_dung ORDER BY c.created_at DESC")
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'communities': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/communities/create')
def api_create_community():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = data.get('description')
    owner_id = data.get('owner_id')
    if not name or not owner_id:
        return jsonify({'status': 'error', 'message': 'Thiếu tên hoặc owner_id'}), 400
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO communities (name, description, owner_id) VALUES (%s,%s,%s)", (name, description, owner_id))
        cid = cursor.lastrowid
        conn.commit()
        return jsonify({'status': 'success', 'id_community': cid})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()



@app.post('/api/communities/<int:id_community>/join')
def api_community_join(id_community):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400
    # ensure community_members table exists
    try:
        create_table_community_members()
    except Exception:
        pass

    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM community_members WHERE id_community=%s AND id_nguoi_dung=%s", (id_community, user_id))
        if cursor.fetchone()[0] > 0:
            return jsonify({'status': 'success', 'message': 'Đã là thành viên'})
        cursor.execute("INSERT INTO community_members (id_community, id_nguoi_dung, role) VALUES (%s,%s,%s)", (id_community, user_id, 'member'))
        conn.commit()
        try:
            # award small activity point
            cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (user_id, 5, 'joined_community', 'community', id_community))
            conn.commit()
        except Exception:
            conn.rollback()
        return jsonify({'status': 'success', 'message': 'Joined community'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/communities/<int:id_community>/leave')
def api_community_leave(id_community):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu user_id'}), 400
    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM community_members WHERE id_community=%s AND id_nguoi_dung=%s", (id_community, user_id))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Left community'})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.get('/api/communities/<int:id_community>/members')
def api_community_members(id_community):
    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT cm.id_member, cm.role, u.id_nguoi_dung, u.ten_dang_nhap, u.email FROM community_members cm JOIN nguoi_dung u ON cm.id_nguoi_dung = u.id_nguoi_dung WHERE cm.id_community = %s ORDER BY cm.joined_at ASC", (id_community,))
        rows = cursor.fetchall() or []
        return jsonify({'status': 'success', 'members': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


@app.post('/api/messages/send')
def api_send_message():
    data = request.get_json() or {}
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    content = data.get('content') or ''
    attachments = data.get('attachments')

    if not sender_id or (not receiver_id and not group_id):
        return jsonify({'status': 'error', 'message': 'Thiếu người nhận/nhóm'}), 400

    # Block if sender is banned
    try:
        if is_user_banned(int(sender_id)):
            return jsonify({'status': 'error', 'message': 'User is banned'}), 403
    except Exception:
        pass

    conn = connect_to_mysql(); cursor = conn.cursor()
    try:
        # rate limit messages per minute
        cursor.execute("SELECT COUNT(*) FROM messages WHERE sender_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)", (sender_id,))
        recent_msgs = cursor.fetchone()[0] or 0
        if recent_msgs >= 30:
            try:
                record_infraction(sender_id, 'message_rate', weight=2)
                auto_escalate_bans(sender_id)
            except Exception:
                pass
            return jsonify({'status': 'error', 'message': 'Bạn gửi quá nhiều tin nhắn. Hãy chờ.'}), 429

        cursor.execute("INSERT INTO messages (sender_id, receiver_id, group_id, content, attachments) VALUES (%s,%s,%s,%s,%s)", (sender_id, receiver_id, group_id, content, json.dumps(attachments, ensure_ascii=False) if attachments else None))
        msgid = cursor.lastrowid
        conn.commit()
        # award activity points and streak for messaging
        try:
            cursor.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (sender_id, 1, 'message_sent', group_id and 'group_message' or 'private_message', msgid))
            conn.commit()
        except Exception:
            try: conn.rollback()
            except: pass
        try:
            # small streak award
            from save_mysql import award_streak_points
            award_streak_points(int(sender_id), points=2)
        except Exception:
            pass
        # basic spam heuristic: many links in a single message
        try:
            if isinstance(content, str) and content.count('http') > 3:
                try:
                    record_infraction(sender_id, 'spam_links', weight=1)
                    auto_escalate_bans(sender_id)
                except Exception:
                    pass
        except Exception:
            pass
        # detect repeated identical messages in short window -> consider spam
        try:
            cur2 = conn.cursor()
            cur2.execute("SELECT COUNT(*) FROM messages WHERE sender_id=%s AND content=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)", (sender_id, content))
            dup_count = cur2.fetchone()[0] or 0
            cur2.close()
            if dup_count >= 5:
                try:
                    record_infraction(sender_id, 'repeated_messages', weight=1)
                    apply_ban(sender_id, level=1, days=None, reason='Auto 30min ban for repeated messages')
                except Exception:
                    pass
        except Exception:
            pass
        # Emit via socketio to receiver or group
        payload = {
            'id_message': msgid,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'group_id': group_id,
            'content': content,
            'attachments': attachments,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        try:
            if group_id:
                socketio.emit('group_message', payload, room=f'group_{group_id}')
            elif receiver_id:
                socketio.emit(f'private_message_{receiver_id}', payload)
        except Exception:
            pass
        return jsonify({'status': 'success', 'id_message': msgid})
    except Exception as e:
        conn.rollback(); return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


# SocketIO handlers
@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'connected'})


@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    # data: { caller_id, callee_id, sdp, call_id }
    try:
        callee = data.get('callee_id')
        caller = data.get('caller_id')
        call_id = data.get('call_id')
        sdp = data.get('sdp')
        if callee:
            emit('webrtc_offer', {'caller_id': caller, 'sdp': sdp, 'call_id': call_id}, room=f'user_{callee}')
    except Exception:
        pass


@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    # data: { caller_id, callee_id, sdp, call_id }
    try:
        caller = data.get('caller_id')
        callee = data.get('callee_id')
        sdp = data.get('sdp')
        if caller:
            emit('webrtc_answer', {'callee_id': callee, 'sdp': sdp}, room=f'user_{caller}')
    except Exception:
        pass


@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice(data):
    # relay ICE candidates between peers
    try:
        target = data.get('target_id')
        candidate = data.get('candidate')
        if target:
            emit('webrtc_ice_candidate', {'candidate': candidate, 'from': data.get('from')}, room=f'user_{target}')
    except Exception:
        pass


@socketio.on('register_user_socket')
def handle_register_user(data):
    # client can call to join personal room for signaling: room name user_<id>
    try:
        uid = data.get('user_id')
        if uid:
            join_room(f'user_{uid}')
    except Exception:
        pass


@socketio.on('join_group')
def handle_join_group(data):
    gid = data.get('group_id')
    uid = data.get('user_id')
    if gid and uid:
        room = f'group_{gid}'
        join_room(room)
        emit('joined_group', {'group_id': gid, 'user_id': uid}, room=room)


@socketio.on('leave_group')
def handle_leave_group(data):
    gid = data.get('group_id')
    uid = data.get('user_id')
    if gid and uid:
        room = f'group_{gid}'
        leave_room(room)
        emit('left_group', {'group_id': gid, 'user_id': uid}, room=room)


@socketio.on('send_message')
def handle_socket_send_message(data):
    # data: sender_id, receiver_id (optional), group_id (optional), content
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    content = data.get('content')

    try:
        if is_user_banned(int(sender_id)):
            emit('message_error', {'message': 'You are banned'})
            return
    except Exception:
        pass

    # rate limit check for socket messages
    try:
        conn_check = connect_to_mysql(); cur_check = conn_check.cursor()
        cur_check.execute("SELECT COUNT(*) FROM messages WHERE sender_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)", (sender_id,))
        recent = cur_check.fetchone()[0] or 0
        cur_check.close(); conn_check.close()
        if recent >= 30:
            try:
                record_infraction(sender_id, 'message_rate', weight=2)
                auto_escalate_bans(sender_id)
            except Exception:
                pass
            emit('message_error', {'message': 'Bạn gửi quá nhiều tin nhắn. Hãy chờ.'})
            return
    except Exception:
        pass

    # persist message
    conn = connect_to_mysql(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO messages (sender_id, receiver_id, group_id, content) VALUES (%s,%s,%s,%s)", (sender_id, receiver_id, group_id, content))
        mid = cur.lastrowid
        conn.commit()
        # award activity points and streak for socket messages
        try:
            cur.execute("INSERT INTO activity_points (user_id, points, reason, related_type, related_id) VALUES (%s,%s,%s,%s,%s)", (sender_id, 1, 'message_sent_socket', group_id and 'group_message' or 'private_message', mid))
            conn.commit()
        except Exception:
            try: conn.rollback()
            except: pass
        try:
            from save_mysql import award_streak_points
            award_streak_points(int(sender_id), points=2)
        except Exception:
            pass
        payload = {'id_message': mid, 'sender_id': sender_id, 'receiver_id': receiver_id, 'group_id': group_id, 'content': content}
        if group_id:
            socketio.emit('group_message', payload, room=f'group_{group_id}')
        elif receiver_id:
            socketio.emit(f'private_message_{receiver_id}', payload)
        # check repeated identical messages for spam (socket)
        try:
            c2 = conn.cursor(); c2.execute("SELECT COUNT(*) FROM messages WHERE sender_id=%s AND content=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)", (sender_id, content)); dcount = c2.fetchone()[0] or 0; c2.close()
            if dcount >= 5:
                try:
                    record_infraction(sender_id, 'repeated_messages', weight=1)
                    apply_ban(sender_id, level=1, days=None, reason='Auto 30min ban for repeated messages')
                except Exception:
                    pass
        except Exception:
            pass
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        emit('message_error', {'message': str(e)})
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


# --- WebRTC signaling events via Socket.IO ---
@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    # data: {from, to, sdp}
    to = data.get('to')
    if not to:
        return
    try:
        socketio.emit(f'webrtc_offer_{to}', data)
    except Exception:
        pass


@socketio.on('webrtc_answer')
def handle_webrtc_answer(data):
    # data: {from, to, sdp}
    to = data.get('to')
    if not to:
        return
    try:
        socketio.emit(f'webrtc_answer_{to}', data)
    except Exception:
        pass


@socketio.on('webrtc_ice')
def handle_webrtc_ice(data):
    # data: {from, to, candidate}
    to = data.get('to')
    if not to:
        return
    try:
        socketio.emit(f'webrtc_ice_{to}', data)
    except Exception:
        pass


@app.get('/api/messages/history')
def api_get_messages_history():
    user_a = request.args.get('user_a')
    user_b = request.args.get('user_b')
    group_id = request.args.get('group_id')
    limit = int(request.args.get('limit') or 100)

    conn = connect_to_mysql(); cursor = conn.cursor(dictionary=True)
    try:
        if group_id:
            cursor.execute("SELECT m.*, u.ten_dang_nhap AS sender_name FROM messages m JOIN nguoi_dung u ON m.sender_id = u.id_nguoi_dung WHERE m.group_id = %s ORDER BY m.created_at ASC LIMIT %s", (group_id, limit))
        else:
            cursor.execute("SELECT m.*, u.ten_dang_nhap AS sender_name FROM messages m JOIN nguoi_dung u ON m.sender_id = u.id_nguoi_dung WHERE ((m.sender_id = %s AND m.receiver_id = %s) OR (m.sender_id = %s AND m.receiver_id = %s)) ORDER BY m.created_at ASC LIMIT %s", (user_a, user_b, user_b, user_a, limit))
        rows = cursor.fetchall() or []
        for r in rows:
            if r.get('attachments'):
                try:
                    r['attachments'] = json.loads(r['attachments'])
                except Exception:
                    pass
        return jsonify({'status': 'success', 'messages': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close(); conn.close()


if __name__ == "__main__":
    startup()
    app.run(debug=True, port=5000, host="0.0.0.0")