from langchain_google_genai import ChatGoogleGenerativeAI
from prompt import BASE_ROLE_PROMPT, PROMPTS, CHATBOT_PROMPT, VOICE_PROMPT
from dotenv import load_dotenv
from flask import Flask, render_template, send_file, jsonify, request
from flask_cors import CORS
import os
import json
from struc_lesson import *
import re
from save_mysql import *
import speech_recognition as sr
from gtts import gTTS
import sounddevice as sd
import scipy.io.wavfile as wav
import pygame
from config_py import startup

load_dotenv()

app = Flask(__name__)
CORS(app)


class EnglishTeachingAgent:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model=model,
            temperature=1
        )

    def generate(self, task: str, **kwargs) -> dict:
        if task not in PROMPTS:
            raise ValueError(f"Nhiệm vụ {task} chưa được định nghĩa trong PROMPTS")

        full_prompt = BASE_ROLE_PROMPT + "\n\n" + PROMPTS[task].format(**kwargs)
        response = self.llm.invoke(full_prompt)

        try:
            result_json = json.loads(response.content)
        except json.JSONDecodeError:
            result_json = {"content": response.content}

        return result_json

API_KEY = os.getenv("GEMINI_API_KEY")
agent = EnglishTeachingAgent(api_key=API_KEY)

# Trang đăng nhập
@app.route('/')
def index():
    return render_template("login.html")

# Trang chủ
@app.route('/home')
def index_page():
    return render_template("index.html")

# Trang voice
@app.route('/voice')
def voice_page():
    return render_template("voice.html")

# Trang bài học
@app.route('/lesson')
def lesson_page():
    return render_template("lesson.html")

# TrangAI  chatbot
@app.route('/chatbot')
def chatbot_page():
    return render_template("chatbot.html")

#//////////////////////////// ADMIN ////////////////////////////////////////////////////
# Trang admin quản lý user
@app.route('/ad_user')
def ad_user():
    return render_template("ad_user.html")

# Trang admin quản lý lesson
@app.route('/ad_lesson')
def ad_lesson():
    return render_template("ad_lesson.html")

# Trang admin quản lý query
@app.route('/ad_query')
def ad_query():
    return render_template("ad_query.html")

#///////////////////////////////////////// AI Lesson TẠO BÀI HỌC //////////////////////////////////
# API tạo bài học
# API tạo bài học
@app.route('/generate/lesson/<topic>', methods=["POST"])
def generate_content(topic):
    try:
        # Lấy dữ liệu từ request JSON
        data = request.get_json()
        id_user = data.get("id_user")

        if not id_user:
            return jsonify({"error": "Thiếu id_user"}), 400

        # Bước 1: Tạo bài học ban đầu từ AI
        print(f"🚀 Bước 1: Tạo bài học ban đầu cho user {id_user}, chủ đề '{topic}'")
        lesson_data = agent.generate("lesson", topic=topic)
        content = lesson_data.get('content', '{}')
        print("🔥 AI raw content:", content)

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
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw content: {content}")
            ai_json = {"topic": topic}

        # Bước 2: Chuẩn hóa cấu trúc và tạo exercises mẫu
        print("🔧 Bước 2: Chuẩn hóa cấu trúc và tạo exercises")
        standardized_lesson = standardize_lesson(ai_json, topic)
        print("✅ Standardized lesson JSON:", json.dumps(standardized_lesson, ensure_ascii=False, indent=2))

        # Bước 3: Đưa bài học đã chuẩn hóa qua AI lần 2 để tối ưu hóa
        print("🎯 Bước 3: Tối ưu hóa bài học qua AI")
        lesson_json_str = json.dumps(standardized_lesson, ensure_ascii=False, indent=2)

        final_lesson_data = agent.generate("finalize_lesson", lesson_data=lesson_json_str)
        final_content = final_lesson_data.get('content', '{}')
        print("🌟 AI final content:", final_content)

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

            print("🎉 Final lesson JSON:", json.dumps(final_result, ensure_ascii=False, indent=2))

            # 🔹 chỗ này bạn có thể gọi insert_ai_lesson(id_user, json.dumps(final_result, ensure_ascii=False)) để lưu DB
            insert_ai_lesson(id_user, topic,final_content, "gemini 2.5")

            return jsonify(final_result)
        except json.JSONDecodeError as e:
            print(f"⚠️ AI không trả về JSON hợp lệ: {e}")
            return jsonify(standardized_lesson)

    except Exception as e:
        print(f"❌ Error generating content: {str(e)}")
        return jsonify({"error": str(e)}), 500

        
#//////////////////////////////// AI CHATBOT DẠY HỌC ////////////////////////////////////////////////////


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    student_input = data.get("message", "")
    id_user = data.get("id_user")

    if not id_user or not student_input:
        print ("❌ Thiếu id_user hoặc message")
        return jsonify({"error": "Thiếu id_user hoặc message"}), 400

    chat_prompt = CHATBOT_PROMPT.replace("{student_input}", student_input)
    response = agent.llm.invoke(chat_prompt)
    print("Raw response:", response)

    content = response.content
    cleaned = re.sub(r"```json\s*|\s*```|\*+", "", content).strip()
    chat_ai = cleaned  # lưu tạm để insert DB

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {"response_english": cleaned}

    result = {
        "response_english": parsed.get("response_english") or "",
        "explanation_vietnamese": parsed.get("explanation_vietnamese") or "",
        "correction": parsed.get("correction") or ""
    }

    # 👉 Insert vào DB ngay khi chat
    ok = insert_ai_chat(id_user, student_input, chat_ai, "gemini 1.5")
    if not ok:
        return jsonify({"error": "Không lưu được dữ liệu"}), 500

    return jsonify(result)


#/////////////////////////// CHẠY ĐĂNG NHẬP mysql /////////////////////////

# API đăng ký
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
   

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Thiếu thông tin đăng ký!"}), 400

    success = insert_new_user(username, email, password)
    if success:
        return jsonify({"status": "success", "message": "Đăng ký thành công!"}), 201
    else:
        return jsonify({"status": "error", "message": "Email đã tồn tại hoặc lỗi khi đăng ký!"}), 400

# API đăng nhập
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Thiếu email hoặc mật khẩu!"}), 400

    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"status": "error", "message": "Lỗi kết nối CSDL"}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(sql, (email, password))
        user = cursor.fetchone()

        if user:
            return jsonify({
                "status": "success",
                "message": "Đăng nhập thành công!",
                "redirect": "/home",
                "id_user": user["id"],       # 🔹 trả id_user
                "username": user["username"],# 🔹 trả username
                "role": user["role"]         # 🔹 trả role
            }), 200
        else:
            return jsonify({"status": "error", "message": "Sai email hoặc mật khẩu!"}), 401
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#/////////////////////// Quyền ADMIN //////////////////////////////////
@app.route("/update_user", methods=["PUT"])
def api_update_user():
    """Cập nhật thông tin user"""
    data = request.get_json()
    user_id = data.get("id")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not all([user_id, username, email, password, role]):
        return jsonify({"status": "error", "message": "Thiếu dữ liệu!"}), 400

    success = update_user(user_id, username, email, password, role)
    if success:
        return jsonify({"status": "success", "message": f"User {user_id} đã cập nhật thành công!"})
    else:
        return jsonify({"status": "error", "message": f"Không thể cập nhật user {user_id}!"}), 500


# ====== API delete user ======
@app.route("/delete_user/<int:user_id>", methods=["DELETE"])
def api_delete_user(user_id):
    success = delete_user(user_id)
    if success:
        print(f"🗑️ User {user_id} đã bị xóa!")
        return jsonify({"status": "success", "message": f"User {user_id} đã bị xóa!"})
    else:
        print(f"❌ Không tìm thấy user {user_id}!")
        return jsonify({"status": "error", "message": f"Không tìm thấy user {user_id}!"}), 404

# ====== API get all users ======
@app.route("/get_all/users", methods=["GET"])
def api_get_users():
    users = show_all_users()
    return jsonify(users), 200

# ====== API add new user (admin) ======
@app.route("/add/users", methods=["POST"])
def api_add_user():
    data = request.get_json()
    username = data.get("username")   # 🔹 sửa "name" -> "username"
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    success, msg = admin_insert_user(username, email, password, role)
    status = "success" if success else "error"
    print(f"➕ Thêm user: {msg}🤡")
    return jsonify({"status": status, "message": msg}), (200 if success else 400)

# API nhận query
@app.route("/run_query", methods=["POST"])
def run_query():
    data = request.get_json()
    sql_query = data.get("query", "").strip()

    if not sql_query:
        return jsonify({"status": "error", "result": "❌ Vui lòng nhập lệnh SQL!"}), 400

    connection = connect_to_mysql()
    if connection is None:
        return jsonify({"status": "error", "result": "❌ Không kết nối được MySQL!"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute(sql_query)

        if sql_query.lower().startswith("select"):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
        else:
            connection.commit()
            result = f"✅ Query thành công! {cursor.rowcount} hàng bị ảnh hưởng."

        return jsonify({"status": "success", "result": result})
    except Error as e:
        return jsonify({"status": "error", "result": f"❌ Lỗi khi thực hiện query: {e}"})
    finally:
        cursor.close()
        connection.close() 

@app.route("/show_all", methods=["GET"])
def api_show_all():
    """API trả về toàn bộ dữ liệu database dưới dạng JSON"""
    data = get_all_tables_data()
    return jsonify({"status": "success", "result": data})


# API thông kê mức độ học tập user
@app.route("/count_lessons_all", methods=["GET"])
def api_count_all_user_lessons():
    data = count_all_user_lessons()
    return jsonify(data)

#////////////////////////// AI voice //////////////////////////////////

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
    global is_recording, recording, id_user
    data = request.get_json()
    id_user = data.get("id_user")   # 🔹 lấy id_user từ frontend

    if not id_user:
        print("❌ Thiếu id_user")
        return jsonify({"status": "error", "message": "Thiếu id_user"}), 400

    if is_recording:
        print("❌ Đang ghi âm rồi!")
        return jsonify({"status": "error", "message": "Đang ghi âm rồi!"}), 400

    print(f"🎤 Bắt đầu ghi âm cho user {id_user}")
    recording = sd.rec(int(10 * fs), samplerate=fs, channels=1, dtype="int16")
    is_recording = True
    return jsonify({"status": "ok", "message": "Bắt đầu ghi âm"})

@app.route("/stop_record", methods=["POST"])
def stop_record():
    global is_recording, recording, id_user
    data = request.get_json()
    id_user = data.get("id_user")   # 🔹 lấy id_user từ frontend

    if not id_user:
        return jsonify({"status": "error", "message": "Thiếu id_user"}), 400

    if not is_recording:
        return jsonify({"status": "error", "message": "Chưa có ghi âm nào đang chạy!"}), 400

    sd.stop()
    wav.write(filename, fs, recording)
    is_recording = False
    print(f"🛑 Dừng ghi âm, lưu vào {filename} cho user {id_user}")

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

    voice_prompt = VOICE_PROMPT.replace("{student_input}", user_text)
    response = agent.llm.invoke(voice_prompt)
    bot_reply = response.content
    print("🤖 Bot:", bot_reply)

    # 🔹 Lưu hội thoại vào DB kèm id_user
    insert_ai_voice(id_user, user_text, bot_reply, "gemini 1.5")

    speak(bot_reply)

    return jsonify({
        "status": "ok",
        "user_text": user_text,
        "bot_reply": bot_reply
    })


#///////////////////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    startup()
    app.run(debug=True, port=5000)