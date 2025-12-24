import mysql.connector
from mysql.connector import Error
import json

# Cấu hình
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "bao123"
DB_NAME = "aichat2"

#////////////// ////////////////////////////////////////////////Tạo database và bảng nếu chưa có//////////////////////////////
# Hàm tạo database nếu chưa có
def create_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"✅ Database `{DB_NAME}` đã sẵn sàng!")
    except Error as e:
        print("❌ Lỗi khi tạo database:", e)


# Hàm tạo bảng nếu chưa có (và thêm cột vai_tro nếu thiếu)
def create_table():
    """Tạo bảng nguoi_dung nếu chưa có, và thêm cột vai_tro nếu thiếu."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Tạo bảng nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nguoi_dung (
                id_nguoi_dung INT AUTO_INCREMENT PRIMARY KEY,
                ten_dang_nhap VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                mat_khau VARCHAR(255) NOT NULL,
                vai_tro ENUM('user','admin') DEFAULT 'user',
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Bảng `nguoi_dung` đã sẵn sàng!")

        # Kiểm tra xem cột vai_tro có tồn tại chưa
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'vai_tro'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN vai_tro ENUM('user','admin') DEFAULT 'user'")
            print("🔧 Đã thêm cột `vai_tro` vào bảng `nguoi_dung`.")

    except Error as e:
        print("❌ Lỗi khi tạo bảng:", e)

# Hàm tạo bảng baihoc
def create_baihoc_table():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baihoc (
                id_baihoc INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                chu_de VARCHAR(255) NOT NULL,
                model_ai VARCHAR(100) DEFAULT 'gemini 2.0',
                noi_dung_baihoc LONGTEXT,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `baihoc` đã sẵn sàng!")
    except Error as e:
        print("❌ Lỗi khi tạo bảng baihoc:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm tạo bảng AI_voice
def create_table_ai_voice():
    """Tạo bảng AI_voice nếu chưa có."""
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AI_voice (
                id_chat BIGINT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_AI VARCHAR(100) DEFAULT 'gemini 2.0',
                tro_chuyen_user LONGTEXT,
                tro_chuyen_ai LONGTEXT,
                CONSTRAINT fk_ai_voice_user FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `AI_voice` đã sẵn sàng!")
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng AI_voice:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# Hàm tạo bảng AI_chat
def create_table_ai_chat():
    """Tạo bảng AI_chat nếu chưa có."""
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AI_chat (
                id_chat BIGINT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_AI VARCHAR(100) DEFAULT 'gemini 2.0',
                noi_dung_user LONGTEXT,
                noi_dung_ai LONGTEXT,
                CONSTRAINT fk_ai_chat_user FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `AI_chat` đã sẵn sàng!")
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng AI_chat:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Hàm tạo bảng bai_kiem_tra
def create_table_bai_kiem_tra():
    """Tạo bảng bai_kiem_tra và các bảng liên quan nếu chưa có."""
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        
        # Tạo bảng bai_kiem_tra
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bai_kiem_tra (
                id_kt INT AUTO_INCREMENT PRIMARY KEY,
                tieu_de VARCHAR(255),
                mo_ta TEXT,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `bai_kiem_tra` đã sẵn sàng!")
        
        # Tạo bảng cauhoi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cauhoi (
                id_cauhoi INT AUTO_INCREMENT PRIMARY KEY,
                noi_dung LONGTEXT,
                loai_cau_hoi ENUM('trac_nghiem','tu_luan','sap_xep','dien_khuyet') DEFAULT 'trac_nghiem',
                muc_do ENUM('de','trung_binh','kho') DEFAULT 'de',
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `cauhoi` đã sẵn sàng!")
        
        # Tạo bảng baiKT_cauhoi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS baiKT_cauhoi (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_kt INT NOT NULL,
                id_cauhoi INT NOT NULL,
                FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt) ON DELETE CASCADE,
                FOREIGN KEY (id_cauhoi) REFERENCES cauhoi(id_cauhoi) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `baiKT_cauhoi` đã sẵn sàng!")
        
        # Tạo bảng dap_an
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dap_an (
                id_dapan INT AUTO_INCREMENT PRIMARY KEY,
                id_cauhoi INT NOT NULL,
                noi_dung VARCHAR(255),
                ketqua BOOLEAN DEFAULT FALSE,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP NULL,
                FOREIGN KEY (id_cauhoi) REFERENCES cauhoi(id_cauhoi) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `dap_an` đã sẵn sàng!")
        
        # Tạo bảng ket_qua_kiem_tra
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ket_qua_kiem_tra (
                id_ket_qua INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                id_kt INT NOT NULL,
                diem FLOAT,
                chi_tiet JSON,
                ngay_lam TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
                FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `ket_qua_kiem_tra` đã sẵn sàng!")
        
        connection.commit()
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng bai_kiem_tra:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

#///////////////////////////////////////////////////////////////////////////// USER//////////////////////////////////////////////////////////////////////

# Hàm kết nối MySQL
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if connection.is_connected():
            print("✅ Kết nối MySQL thành công!")
            return connection
    except Error as e:
        print("❌ Lỗi kết nối MySQL:", e)
    return None

# Hàm thêm user (mặc định vai_tro = user)
def insert_new_user(ten_dang_nhap, email, mat_khau):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        # Kiểm tra trùng email
        cursor.execute("SELECT COUNT(*) FROM nguoi_dung WHERE email = %s", (email,))
        if cursor.fetchone()[0] > 0:
            print(f"⚠️ Email '{email}' đã tồn tại trong hệ thống.")
            return False

        sql = "INSERT INTO nguoi_dung (ten_dang_nhap, email, mat_khau, vai_tro) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (ten_dang_nhap, email, mat_khau, "user"))
        connection.commit()
        print("✅ Thêm user mới thành công (vai_tro=user)!")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm user:", e)
        return False

        
# Hàm đăng nhập user
def login_user(email, mat_khau):
    """Kiểm tra email và mat_khau, vai_tro"""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dict thay vì tuple
        sql = "SELECT * FROM nguoi_dung WHERE email = %s AND mat_khau = %s"
        cursor.execute(sql, (email, mat_khau))
        result = cursor.fetchone()
        if result:
            print(f"✅ Đăng nhập thành công! Xin chào {result['ten_dang_nhap']} (vai_tro={result['vai_tro']})")
        else:
            print("❌ Đăng nhập thất bại!")
        return result
    except Error as e:
        print("❌ Lỗi khi kiểm tra user:", e)
        return None

def insert_ai_lesson(id_nguoi_dung, chu_de, noi_dung_baihoc, model_ai="gemini 2.0"):
    """ lưu lại bài học của user vào bảng baihoc """
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO baihoc (id_nguoi_dung, chu_de, model_ai, noi_dung_baihoc)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_nguoi_dung, chu_de, model_ai, noi_dung_baihoc))
        connection.commit()
        print(f"✅ Bài học mới đã được thêm cho user_id={id_nguoi_dung}, chu_de={chu_de}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm bài học:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# Hàm tạo bảng OTP_dang_ky_email (lưu OTP đăng ký)
def create_table_xac_thuc_email():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OTP_dang_ky_email (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) NOT NULL,
                ten_dang_nhap VARCHAR(100) NOT NULL,
                mat_khau VARCHAR(255) NOT NULL,
                ma_otp VARCHAR(6) NOT NULL,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `OTP_dang_ky_email` đã sẵn sàng!")
        return True

    except Error as e:
        print("❌ Lỗi khi tạo bảng OTP_dang_ky_email:", e)
        return False
    
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Hàm tạo bảng otp_quen_mat_khau
def create_table_otp_quen_mat_khau():
    """Tạo bảng otp_quen_mat_khau nếu chưa có."""
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_quen_mat_khau (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) NOT NULL UNIQUE,
                otp VARCHAR(6) NOT NULL,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `otp_quen_mat_khau` đã sẵn sàng!")
        return True

    except Error as e:
        print("❌ Lỗi khi tạo bảng otp_quen_mat_khau:", e)
        return False
    
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Hàm lưu OTP vào bảng otp_quen_mat_khau (Quên mk)
def save_otp(email, otp):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()

        # Kiểm tra email đã có chưa
        cursor.execute("SELECT * FROM otp_quen_mat_khau WHERE email=%s", (email,))
        result = cursor.fetchone()

        if result:
            cursor.execute("UPDATE otp_quen_mat_khau SET otp=%s WHERE email=%s", (otp, email))
        else:
            cursor.execute("INSERT INTO otp_quen_mat_khau (email, otp) VALUES (%s, %s)", (email, otp))

        conn.commit()
        print("✅ Lưu OTP thành công!")
        return True
    except Exception as e:
        print("❌ Lỗi lưu OTP:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Hàm thêm dữ liệu vào bảng AI_chat
def insert_ai_chat(id_nguoi_dung, noi_dung_user, noi_dung_ai, model_ai="gemini 2.0"):
    """Lưu hội thoại dạng text vào bảng AI_chat."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO AI_chat (id_nguoi_dung, noi_dung_user, noi_dung_ai, model_ai)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_nguoi_dung, noi_dung_user, noi_dung_ai, model_ai))
        connection.commit()
        print(f"✅ Hội thoại mới đã được thêm cho user_id={id_nguoi_dung}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm AI_chat:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# Hàm thêm dữ liệu vào bảng AI_voice
def insert_ai_voice(id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai="gemini 2.0"):
    """Lưu hội thoại dạng giọng nói vào bảng AI_voice."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO AI_voice (id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai))
        connection.commit()
        print(f"✅ Voice mới đã được thêm cho user_id={id_nguoi_dung}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm AI_voice:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def count_all_user_baihoc():
    """Trả về danh sách {id_nguoi_dung, total_baihoc} của tất cả user"""
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)  # dùng dictionary để dễ map JSON
        sql = """
            SELECT u.id_nguoi_dung AS id_nguoi_dung, u.ten_dang_nhap, COUNT(l.id_baihoc) AS total_baihoc
            FROM nguoi_dung u
            LEFT JOIN baihoc l ON u.id_nguoi_dung = l.id_nguoi_dung
            GROUP BY u.id_nguoi_dung, u.ten_dang_nhap
            ORDER BY total_baihoc DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        print("📊 Thống kê số chu_de của tất cả user:", results)
        return results
    except Error as e:
        print("❌ Lỗi khi thống kê bài học:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ///////////////////////////////// BÀI KIỂM TRA ///////////////////////////////////////////
def create_exam_db(tieu_de, mo_ta, cau_hoi_list):
    # Đảm bảo các bảng tồn tại
    create_table_bai_kiem_tra()
    
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO bai_kiem_tra (tieu_de, mo_ta) VALUES (%s, %s)",
            (tieu_de, mo_ta)
        )
        id_kt = cursor.lastrowid

        for q in cau_hoi_list:
            noi_dung = (q.get("noi_dung") or "").strip()
            loai = (q.get("loai_cau_hoi") or "").strip()
            muc_do = (q.get("muc_do") or "de").strip()
            dap_an = q.get("dap_an") or []

            if not noi_dung:
                raise ValueError("Câu hỏi thiếu nội dung")

            if loai not in ("trac_nghiem", "tu_luan"):
                raise ValueError("Loại câu hỏi không hợp lệ (chỉ trac_nghiem/tu_luan)")

            cursor.execute(
                "INSERT INTO cauhoi (noi_dung, loai_cau_hoi, muc_do) VALUES (%s, %s, %s)",
                (noi_dung, loai, muc_do)
            )
            id_cauhoi = cursor.lastrowid

            cursor.execute(
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
                    cursor.execute(
                        "INSERT INTO dap_an (id_cauhoi, noi_dung, ketqua) VALUES (%s, %s, %s)",
                        (id_cauhoi, nd, is_correct)
                    )

            else:  # tu_luan
                ans = ""
                if isinstance(dap_an, list) and len(dap_an) > 0:
                    ans = (dap_an[0].get("noi_dung") or "").strip()
                if not ans:
                    raise ValueError("Tự luận phải có 1 đáp án đúng")

                cursor.execute(
                    "INSERT INTO dap_an (id_cauhoi, noi_dung, ketqua) VALUES (%s, %s, %s)",
                    (id_cauhoi, ans, True)
                )

        connection.commit()
        return id_kt

    except Exception as e:
        print("❌ Lỗi create_exam_db:", e)
        connection.rollback()
        return None
    finally:
        try:
            cursor.close()
            connection.close()
        except Exception:
            pass



def get_exam_detail(id_kt):
    """Lấy thông tin bài kiểm tra kèm câu hỏi và đáp án."""

    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_kt, tieu_de, mo_ta, ngay_tao, ngay_cap_nhat FROM bai_kiem_tra WHERE id_kt=%s",
            (id_kt,),
        )
        exam = cursor.fetchone()
        if not exam:
            return None

        cursor.execute(
            """
            SELECT ch.id_cauhoi, ch.noi_dung, ch.loai_cau_hoi, ch.muc_do
            FROM cauhoi ch
            INNER JOIN baiKT_cauhoi bk ON bk.id_cauhoi = ch.id_cauhoi
            WHERE bk.id_kt = %s
            ORDER BY ch.id_cauhoi
            """,
            (id_kt,),
        )
        questions = cursor.fetchall()

        if not questions:
            exam["cau_hoi"] = []
            return exam

        question_ids = [q["id_cauhoi"] for q in questions]
        format_strings = ",".join(["%s"] * len(question_ids))
        cursor.execute(
            f"""
            SELECT id_dapan, id_cauhoi, noi_dung, ketqua
            FROM dap_an
            WHERE id_cauhoi IN ({format_strings})
            ORDER BY id_dapan
            """,
            question_ids,
        )
        answers = cursor.fetchall()

        answers_by_question = {}
        for ans in answers:
            answers_by_question.setdefault(ans["id_cauhoi"], []).append(ans)

        for q in questions:
            q["dap_an"] = answers_by_question.get(q["id_cauhoi"], [])

        exam["cau_hoi"] = questions
        return exam
    except Error as e:
        print("❌ Lỗi khi lấy thông tin bài kiểm tra:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def submit_exam(id_nguoi_dung, id_kt, bai_lam):
    """Chấm điểm bài kiểm tra và lưu kết quả.

 bai_lam: list[dict] gồm {"id_cauhoi": int, "dap_an_da_chon": [id_dapan, ...], "tra_loi_tu_luan": str}    """

    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)

        cauhoi_ids = [item.get("id_cauhoi") for item in bai_lam if item.get("id_cauhoi")]
        if not cauhoi_ids:
            print("⚠️ Không có câu hỏi nào trong bài làm")
            return None

        format_strings = ",".join(["%s"] * len(cauhoi_ids))
        cursor.execute(
f"""
            SELECT ch.id_cauhoi, ch.loai_cau_hoi, da.id_dapan, da.noi_dung, da.ketqua
            FROM cauhoi ch
            LEFT JOIN dap_an da ON ch.id_cauhoi = da.id_cauhoi
            WHERE ch.id_cauhoi IN ({format_strings})
            """,            cauhoi_ids,
        )
        question_map = {}
        for row in cursor.fetchall():
            qid = row.get("id_cauhoi")
            loai = (row.get("loai_cau_hoi") or "").lower()
            info = question_map.setdefault(
                qid,
                {"loai": loai, "dap_an_trac_nghiem": set(), "dap_an_tu_luan": None},
            )

            if loai == "tu_luan" and row.get("ketqua"):
                info["dap_an_tu_luan"] = (row.get("noi_dung") or "").strip()
            elif row.get("ketqua"):
                info["dap_an_trac_nghiem"].add(row.get("id_dapan"))

        total = len(cauhoi_ids)
        correct_count = 0
        chi_tiet = []

        for item in bai_lam:
            qid = item.get("id_cauhoi")
            info = question_map.get(qid, {})
            loai = (info.get("loai") or "").lower()

            if loai == "tu_luan":
                user_answer = (item.get("tra_loi_tu_luan") or "").strip()
                correct_text = (info.get("dap_an_tu_luan") or "").strip()
                is_correct = bool(correct_text) and user_answer.lower() == correct_text.lower()

                if is_correct:
                    correct_count += 1

                chi_tiet.append(
                    {
                        "id_cauhoi": qid,
                        "tra_loi_tu_luan": user_answer,
                        "dap_an_dung": correct_text,
                        "dung": is_correct,
                    }
                )
                continue
            selected = set(item.get("dap_an_da_chon", []))
            correct_answers = info.get("dap_an_trac_nghiem", set())
            is_correct = selected == correct_answers and len(correct_answers) > 0
            if is_correct:
                correct_count += 1

            chi_tiet.append(
                {
                    "id_cauhoi": qid,
                    "dap_an_chon": list(selected),
                    "dap_an_dung": list(correct_answers),
                    "dung": is_correct,
                }
            )

        diem = round((correct_count / total) * 10, 2) if total else 0

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO ket_qua_kiem_tra (id_nguoi_dung, id_kt, diem, chi_tiet)
            VALUES (%s, %s, %s, %s)
            """,
            (id_nguoi_dung, id_kt, diem, json.dumps(chi_tiet, ensure_ascii=False)),
        )
        connection.commit()

        print(
            f"✅ Lưu kết quả kiểm tra: id_nguoi_dung={id_nguoi_dung}, id_kt={id_kt}, diem={diem} ({correct_count}/{total})"
        )
        return {"diem": diem, "tong_cau": total, "so_cau_dung": correct_count, "chi_tiet": chi_tiet}
    except Error as e:
        print("❌ Lỗi khi chấm bài kiểm tra:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#//////////////////////////////////////////////////////////////// ADMIN    //////////////////////////////////////////////////////////////
 ## Thêm user mới với quyền admin.
def admin_insert_user(ten_dang_nhap, email, mat_khau, vai_tro):
    connection = connect_to_mysql()
    if connection is None:
        return False, "Lỗi kết nối CSDL"

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO nguoi_dung (ten_dang_nhap, email, mat_khau, vai_tro) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (ten_dang_nhap, email, mat_khau, vai_tro))
        connection.commit()
        return True, f"Thêm user '{ten_dang_nhap}' thành công (vai_tro={vai_tro})!"
    except Error as e:
        return False, f"Lỗi khi thêm user: {e}"

        
# Hàm update thông tin user
def update_user(user_id, ten_dang_nhap, email, mat_khau, vai_tro):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            UPDATE nguoi_dung
            SET ten_dang_nhap = %s, email = %s, mat_khau = %s, vai_tro = %s
            WHERE id_nguoi_dung = %s
        """
        cursor.execute(sql, (ten_dang_nhap, email, mat_khau, vai_tro, user_id))
        connection.commit()

        if cursor.rowcount > 0:
            print(f"✅ User ID {user_id} đã được cập nhật!")
            return True
        else:
            print(f"⚠️ Không tìm thấy user ID {user_id} để cập nhật.")
            return False
    except Error as e:
        print("❌ Lỗi khi update user:", e)
        return False



# Hàm xóa user
def delete_user(user_id):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "DELETE FROM nguoi_dung WHERE id_nguoi_dung = %s"
        cursor.execute(sql, (user_id,))
        connection.commit()

        if cursor.rowcount > 0:
            print(f"🗑️ User ID {user_id} đã bị xóa!")
            return True
        else:
            print(f"⚠️ Không tìm thấy user ID {user_id} để xóa.")
            return False
    except Error as e:
        print("❌ Lỗi khi xóa user:", e)
        return False


# Hàm xem toàn bộ người dùng trong bảng nguoi_dung
def show_all_nguoi_dung():
    """Lấy tất cả user trong bảng nguoi_dung."""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dạng dict
        cursor.execute("SELECT * FROM nguoi_dung")
        rows = cursor.fetchall()
        print(f"👥 Tìm thấy {len(rows)} user.")
        return rows if rows else []

    except Error as e:
        print("❌ Lỗi khi truy vấn dữ liệu:", e)
        return None

# Hàm lấy toàn bộ dữ liệu tất cả bảng trong database
def get_all_tables_data():
    """Lấy toàn bộ dữ liệu tất cả bảng trong database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            all_data = []

            for table in tables:
                # key tên cột của dict trả về tùy driver, nên lấy value đầu tiên
                table_name = list(table.values())[0] if isinstance(table, dict) else table[0]
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                all_data.append({
                    "table": table_name,
                    "columns": list(rows[0].keys()) if rows else [],
                    "rows": rows
                })
            print(f"✅ Lấy dữ liệu từ {len(tables)} bảng thành công.")
            return all_data
    except Error as e:
        print(f"Lỗi: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm tạo bảng lich_su_chat (lưu lịch sử chat 5 câu gần nhất)
def create_table_lich_su_chat():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lich_su_chat (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                vai_tro VARCHAR(10) NOT NULL,
                noi_dung LONGTEXT,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `lich_su_chat` đã sẵn sàng!")
        return True

    except Error as e:
        print("❌ Lỗi khi tạo bảng lich_su_chat:", e)
        return False

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



# Lưu tin nhắn
def save_message(id_nguoi_dung, vai_tro, noi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        sql = "INSERT INTO lich_su_chat (id_nguoi_dung, vai_tro, noi_dung) VALUES (%s, %s, %s)"
        cursor.execute(sql, (id_nguoi_dung, vai_tro, noi_dung))
        conn.commit()
    except Exception as e:
        print("❌ Lỗi lưu noi_dung:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Lấy lịch sử chat gần nhất
def get_lich_su_chat(id_nguoi_dung, limit=5):
    history = []
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        sql = "SELECT vai_tro, noi_dung FROM lich_su_chat WHERE id_nguoi_dung=%s ORDER BY ngay_tao DESC LIMIT %s"
        cursor.execute(sql, (id_nguoi_dung, limit))
        rows = cursor.fetchall()
        history = rows[::-1]  # đảo lại để chat cũ lên trước
    except Exception as e:
        print("❌ Lỗi lấy lịch sử:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return history


# Lấy lịch sử làm bài kiểm tra của user
def get_exam_history(id_nguoi_dung, limit=10):
    """Lấy lịch sử làm bài kiểm tra của user.
    
    Args:
        id_nguoi_dung: ID của người dùng
        limit: Số lượng bài tối đa cần lấy (mặc định 10)
        
    Returns:
        list: Danh sách lịch sử làm bài với thông tin: [id_ket_qua, tieu_de, diem, tong_cau, so_cau_dung, ngay_lam, chi_tiet]
    """
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT 
                kq.id_ket_qua,
                kq.id_kt,
                bk.tieu_de,
                kq.diem,
                kq.chi_tiet,
                kq.ngay_lam
            FROM ket_qua_kiem_tra kq
            INNER JOIN bai_kiem_tra bk ON kq.id_kt = bk.id_kt
            WHERE kq.id_nguoi_dung = %s
            ORDER BY kq.ngay_lam DESC
            LIMIT %s
            """,
            (id_nguoi_dung, limit)
        )
        
        results = cursor.fetchall()
        
        # Xử lý dữ liệu trả về
        history = []
        for result in results:
            chi_tiet = result.get('chi_tiet')
            if isinstance(chi_tiet, str):
                try:
                    chi_tiet = json.loads(chi_tiet)
                except:
                    chi_tiet = []
            
            # Đếm số câu đúng
            so_cau_dung = sum(1 for item in chi_tiet if item.get('dung', False))
            tong_cau = len(chi_tiet)
            
            history.append({
                'id_ket_qua': result['id_ket_qua'],
                'id_kt': result['id_kt'],
                'tieu_de': result['tieu_de'],
                'diem': result['diem'],
                'tong_cau': tong_cau,
                'so_cau_dung': so_cau_dung,
                'ngay_lam': result['ngay_lam'].isoformat() if result['ngay_lam'] else None,
                'chi_tiet': chi_tiet
            })
        
        return history
    except Error as e:
        print("❌ Lỗi khi lấy lịch sử làm bài:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# # Test
# if __name__ == "__main__":
#     create_database()   # 🔹 tạo DB nếu chưa có
#     # create_table()      # 🔹 tạo bảng nếu chưa có
#     # insert_new_user("bao", "bao123@gmail.com", "123")
#     # login_user("hoang123@gmail.com", "123456")
#     create_table_ai_voice() # tạo bảng AI_voice
#     create_table_ai_chat()  # tạo bảng AI_chat
#     create_baihoc_table() # Tạo bảng baihoc
#     # insert_lesson(3, "súng ống", "Nội dung bài học về súng ống ")
    
#     # # Thêm hội thoại text
#     # insert_ai_chat(3, "Hello AI!", "Xin chào, tôi là Hoang.")

#     # # Thêm hội thoại voice
#     # insert_ai_voice(3, "hi, i am Hoang", "voice_ai_data_base64_or_text")
#     # show_all_nguoi_dung()
#     total_chu_des = count_all_user_baihoc()