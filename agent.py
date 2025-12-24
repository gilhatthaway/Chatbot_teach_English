from langchain_google_genai import ChatGoogleGenerativeAI
from prompt import BASE_ROLE_PROMPT, PROMPTS, CHATBOT_PROMPT, VOICE_PROMPT
from dotenv import load_dotenv
from flask import Flask, render_template, send_file, jsonify, request, redirect
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
from send_mail import send_otp
import random
from memory import conversation_memory
load_dotenv()

app = Flask(__name__)
CORS(app)


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

# Trang lịch sử tạo bài học
@app.route("/history_page")
def history_page():
    return render_template("history.html")

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

    # ✅ Lưu câu user vào database
    save_message(id_nguoi_dung, "user", student_input)

    # ✅ Lấy ngữ cảnh thông minh từ Memory (recent + semantic)
    try:
        full_context = conversation_memory.get_full_context(id_nguoi_dung, student_input)
    except Exception as e:
        print(f"⚠️ Lỗi lấy context từ memory: {e}")
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
    response = agent.llm.invoke(chat_prompt)
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

    # ✅ Nội dung để lưu DB (KHÔNG lưu JSON thô)
    noi_dung_ai = result["response_english"] + "\n" + result["explanation_vietnamese"]

    # ✅ Lưu vào bảng lịch sử chat
    save_message(id_nguoi_dung, "ai", noi_dung_ai)

    # ✅ Lưu vào bảng AI_chat
    insert_ai_chat(id_nguoi_dung, student_input, noi_dung_ai, "gemini 1.5")

    # ✅ Lưu vào Memory để sử dụng ngữ cảnh thông minh lần sau
    try:
        conversation_memory.add_message(id_nguoi_dung, student_input, noi_dung_ai)
        print(f"✅ Lưu tin nhắn vào Memory cho user {id_nguoi_dung}")
    except Exception as e:
        print(f"⚠️ Lỗi lưu vào Memory: {e}")

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
@app.route("/login", methods=["POST"])
def login():
    print("🔥 LOGIN API HIT")

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
        print("❌ ERROR:", e)
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
        print(f"🚀 Bước 1: Tạo bài học ban đầu cho user {id_nguoi_dung}, chủ đề '{topic}'")
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

             # Đảm bảo dữ liệu trả về cho frontend luôn theo cấu trúc chuẩn
            final_standardized = standardize_lesson(final_result, topic)
            final_json_str = json.dumps(final_standardized, ensure_ascii=False)
            
            insert_ai_lesson(id_nguoi_dung, topic, final_json_str, "gemini 2.5")

            return jsonify(final_standardized)
    
        except json.JSONDecodeError as e:
            print(f"⚠️ AI không trả về JSON hợp lệ: {e}")
            return jsonify(standardized_lesson)

    except Exception as e:
        print(f"❌ Error generating content: {str(e)}")
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
    print(f"🛑 Dừng ghi âm, lưu vào {filename} cho user {id_nguoi_dung}")

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
    
    response = agent.llm.invoke(voice_prompt)
    bot_reply = response.content
    print("🤖 Bot:", bot_reply)

    # ✅ Lưu hội thoại vào DB kèm id_nguoi_dung
    insert_ai_voice(id_nguoi_dung, user_text, bot_reply, "gemini 1.5")

    # ✅ Lưu vào Memory để sử dụng ngữ cảnh lần sau
    try:
        conversation_memory.add_message(id_nguoi_dung, user_text, bot_reply)
        print(f"✅ Lưu tin nhắn voice vào Memory cho user {id_nguoi_dung}")
    except Exception as e:
        print(f"⚠️ Lỗi lưu vào Memory: {e}")

    speak(bot_reply)

    return jsonify({
        "status": "ok",
        "user_text": user_text,
        "bot_reply": bot_reply
    })
#/////////////////////////// BÀI KIỂM TRA /////////////////////////

@app.route("/create/exams", methods=["POST"])
def api_create_exam():
    payload = request.get_json() or {}

    tieu_de = (payload.get("tieu_de") or "").strip()
    mo_ta = (payload.get("mo_ta") or "").strip()
    cau_hoi_list = payload.get("cau_hoi") or []

    if not tieu_de or not isinstance(cau_hoi_list, list) or len(cau_hoi_list) == 0:
        return jsonify({"message": "Thiếu tiêu đề hoặc danh sách câu hỏi"}), 400

    new_id = create_exam_db(tieu_de, mo_ta, cau_hoi_list)
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
                b.ngay_tao,
                COUNT(bk.id_cauhoi) AS so_cau
            FROM bai_kiem_tra b
            LEFT JOIN baiKT_cauhoi bk ON bk.id_kt = b.id_kt
            GROUP BY b.id_kt, b.tieu_de, b.mo_ta, b.ngay_tao
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
            "UPDATE bai_kiem_tra SET tieu_de=%s, mo_ta=%s, ngay_cap_nhat=NOW() WHERE id_kt=%s",
            (tieu_de, mo_ta, id_kt)
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
            dap_an = q.get("dap_an") or []

            if not noi_dung:
                raise ValueError("Câu hỏi thiếu nội dung")
            if loai not in ("trac_nghiem", "tu_luan"):
                raise ValueError("Loại câu hỏi không hợp lệ")

            cursor2.execute(
                "INSERT INTO cauhoi (noi_dung, loai_cau_hoi, muc_do) VALUES (%s, %s, %s)",
                (noi_dung, loai, muc_do)
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
    if result:
        return jsonify({"status": "success", "diem": result.get("diem", 0), "message": "Nộp bài thành công"})
    else:
        return jsonify({"status": "error", "message": "Lỗi khi nộp bài"}), 500

@app.get("/exam/history/<int:id_nguoi_dung>")
def api_get_exam_history(id_nguoi_dung):
    """API endpoint lấy lịch sử làm bài kiểm tra của user"""
    limit = request.args.get("limit", 10, type=int)
    
    from save_mysql import get_exam_history
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
if __name__ == "__main__":
    startup()
    app.run(debug=True, port=5000, host="0.0.0.0")