import mysql.connector
from mysql.connector import Error
import json
from datetime import date, datetime, timedelta
import random
import logging

# module logger
logger = logging.getLogger(__name__)
import builtins

# Redirect module-level prints to structured logging to avoid editing many print sites.
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

# Cấu hình
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = ""
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
        logger.info(f"✅ Database `{DB_NAME}` đã sẵn sàng!")
    except Error as e:
        logger.exception("❌ Lỗi khi tạo database: %s", e)


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
        logger.info("✅ Bảng `nguoi_dung` đã sẵn sàng!")

        # Kiểm tra xem cột vai_tro có tồn tại chưa
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'vai_tro'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN vai_tro ENUM('user','admin') DEFAULT 'user'")
            logger.info("🔧 Đã thêm cột `vai_tro` vào bảng `nguoi_dung`.")

        # Kiểm tra cột streak_count
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'streak_count'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN streak_count INT DEFAULT 0")
            logger.info("🔧 Đã thêm cột `streak_count` vào bảng `nguoi_dung`.")

        # Kiểm tra cột last_streak_date
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'last_streak_date'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN last_streak_date DATE NULL")
            logger.info("🔧 Đã thêm cột `last_streak_date` vào bảng `nguoi_dung`.")

        # Kiểm tra cột streak_points
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'streak_points'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN streak_points INT DEFAULT 0")
            logger.info("🔧 Đã thêm cột `streak_points` vào bảng `nguoi_dung`.")

        # Kiểm tra cột last_streak_action
        cursor.execute("SHOW COLUMNS FROM nguoi_dung LIKE 'last_streak_action'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE nguoi_dung ADD COLUMN last_streak_action DATETIME NULL")
            logger.info("🔧 Đã thêm cột `last_streak_action` vào bảng `nguoi_dung`.")

    except Error as e:
        logger.exception("❌ Lỗi khi tạo bảng: %s", e)

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
        logger.info("✅ Bảng `baihoc` đã sẵn sàng!")
    except Error as e:
        logger.exception("❌ Lỗi khi tạo bảng baihoc: %s", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm tạo bảng flashcard reward cho top users
def create_table_flashcard_rewards():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcard_rewards (
                id_reward INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                tu_vung VARCHAR(100) NOT NULL,
                y_nghia VARCHAR(255) NOT NULL,
                ly_do VARCHAR(255) DEFAULT 'Top 10 streak reward',
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_reward_user FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        logger.info("✅ Bảng `flashcard_rewards` đã sẵn sàng!")
        return True
    except Error as e:
        logger.exception("❌ Lỗi khi tạo bảng flashcard_rewards: %s", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def create_table_quiz_documents():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_documents (
                id_document INT AUTO_INCREMENT PRIMARY KEY,
                tieu_de VARCHAR(255) NOT NULL,
                noi_dung LONGTEXT NOT NULL,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng quiz_documents:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def create_table_quizzes():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id_quiz INT AUTO_INCREMENT PRIMARY KEY,
                tieu_de VARCHAR(255) NOT NULL,
                mo_ta VARCHAR(255) DEFAULT '',
                so_cau INT DEFAULT 0,
                duration_minutes INT DEFAULT 20,
                source_documents JSON,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Thêm cột duration_minutes nếu chưa có
        try:
            cursor.execute("ALTER TABLE quizzes ADD COLUMN duration_minutes INT DEFAULT 20")
        except Error:
            pass  # Cột đã tồn tại
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng quizzes:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def create_table_quiz_questions():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id_question INT AUTO_INCREMENT PRIMARY KEY,
                id_quiz INT NOT NULL,
                loai_quiz VARCHAR(50) DEFAULT 'multiple_choice',
                phan_loai ENUM('vocabulary','grammar') DEFAULT 'vocabulary',
                noi_dung LONGTEXT NOT NULL,
                options JSON,
                dap_an JSON,
                giai_thich LONGTEXT,
                hint VARCHAR(255),
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_quiz) REFERENCES quizzes(id_quiz) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng quiz_questions:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def create_table_quiz_results():
    try:
        connection = connect_to_mysql()
        if connection is None:
            return False

        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id_result INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL,
                id_quiz INT NOT NULL,
                diem FLOAT DEFAULT 0,
                correct_count INT DEFAULT 0,
                total_questions INT DEFAULT 0,
                chi_tiet JSON,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
                FOREIGN KEY (id_quiz) REFERENCES quizzes(id_quiz) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        return True
    except Error as e:
        print("❌ Lỗi khi tạo bảng quiz_results:", e)
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def insert_quiz_document(tieu_de, noi_dung):
    create_table_quiz_documents()
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO quiz_documents (tieu_de, noi_dung) VALUES (%s, %s)",
            (tieu_de, noi_dung)
        )
        connection.commit()
        return cursor.lastrowid
    except Error as e:
        print("❌ Lỗi khi thêm tài liệu quiz:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def create_table_community_members():
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
            CREATE TABLE IF NOT EXISTS community_members (
                id_member INT AUTO_INCREMENT PRIMARY KEY,
                id_community INT NOT NULL,
                id_nguoi_dung INT NOT NULL,
                role ENUM('member','admin','owner') DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_community) REFERENCES communities(id_community) ON DELETE CASCADE,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        return True
    except Exception as e:
        logger.exception('Error creating community_members table: %s', e)
        return False
    finally:
        try:
            if connection.is_connected():
                cursor.close(); connection.close()
        except:
            pass


def record_infraction(user_id, reason='unknown', weight=1):
    try:
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO infractions (user_id, reason, weight) VALUES (%s,%s,%s)", (user_id, reason, weight))
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        logger.exception('Error recording infraction: %s', e)
        try:
            cur.close(); conn.close()
        except:
            pass
        return False


def get_infraction_count(user_id, days=365):
    try:
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM infractions WHERE user_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)", (user_id, days))
        cnt = cur.fetchone()[0] or 0
        cur.close(); conn.close()
        return int(cnt)
    except Exception as e:
        logger.exception('Error getting infraction count: %s', e)
        try:
            cur.close(); conn.close()
        except:
            pass
        return 0


def apply_ban(user_id, level=1, days=None, reason=''):
    try:
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = conn.cursor()
        if level >= 6:
            # permanent ban -> end_at NULL
            cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),NULL,1)", (user_id, level, reason))
        else:
            # Use explicit intervals per level to match policy:
            # level 1: 30 minutes, level 2: 1 hour, level 3: 7 days, level 4: 30 days, level 5: 365 days
            if level == 1:
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 30 MINUTE),1)", (user_id, level, reason))
            elif level == 2:
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 1 HOUR),1)", (user_id, level, reason))
            elif level == 3:
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 7 DAY),1)", (user_id, level, reason))
            elif level == 4:
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 30 DAY),1)", (user_id, level, reason))
            elif level == 5:
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 365 DAY),1)", (user_id, level, reason))
            else:
                # fallback 1 day
                cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),DATE_ADD(NOW(), INTERVAL 1 DAY),1)", (user_id, level, reason))
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        logger.exception('Error applying ban: %s', e)
        try:
            cur.close(); conn.close()
        except:
            pass
        return False


def is_user_banned(user_id):
    try:
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id_ban, level, reason, start_at, end_at FROM bans WHERE user_id=%s AND active=1 ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return False
        end_at = row[4]
        if end_at is None:
            return True
        try:
            from datetime import datetime
            if isinstance(end_at, datetime):
                return end_at > datetime.now()
            # fallback: treat as banned
            return True
        except Exception:
            return True
    except Exception as e:
        logger.exception('Error checking ban: %s', e)
        try:
            cur.close(); conn.close()
        except:
            pass
        return False


def auto_escalate_bans(user_id):
    # Determine infractions count and apply ban level accordingly
    try:
        count = get_infraction_count(user_id, days=365)
        # Map count to level: 1 -> 1, 2 -> 2, 3->3, 4->4, 5->5, >=6->6
        level = min(max(1, count), 6)
        # apply ban by level (apply_ban uses explicit durations)
        if level >= 6:
            return apply_ban(user_id, level=6, days=None, reason=f'Auto-escalation to level {level} based on {count} infractions')
        else:
            return apply_ban(user_id, level=level, days=None, reason=f'Auto-escalation to level {level} based on {count} infractions')
    except Exception as e:
        logger.exception('Error in auto_escalate_bans: %s', e)
        return False


def create_table_follows_and_blocks():
    try:
        connection = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                id_follow INT AUTO_INCREMENT PRIMARY KEY,
                follower_id INT NOT NULL,
                followee_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
                FOREIGN KEY (followee_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id_block INT AUTO_INCREMENT PRIMARY KEY,
                blocker_id INT NOT NULL,
                blocked_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (blocker_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
                FOREIGN KEY (blocked_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        connection.commit()
        cursor.close(); connection.close()
        return True
    except Exception as e:
        logger.exception('Error creating follows/blocks tables: %s', e)
        try:
            cursor.close(); connection.close()
        except:
            pass
        return False


def create_table_admin_actions():
    try:
        connection = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_actions (
                id_action INT AUTO_INCREMENT PRIMARY KEY,
                admin_id INT NULL,
                action_type VARCHAR(128),
                target_type VARCHAR(64),
                target_id INT NULL,
                details LONGTEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        connection.commit()
        cursor.close(); connection.close()
        return True
    except Exception as e:
        logger.exception('Error creating admin_actions table: %s', e)
        try:
            cursor.close(); connection.close()
        except:
            pass
        return False


def get_quiz_documents(limit=50):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_document, tieu_de, noi_dung, ngay_tao FROM quiz_documents ORDER BY ngay_tao DESC LIMIT %s",
            (limit,)
        )
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi khi lấy tài liệu quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def create_quiz_from_questions(tieu_de, mo_ta, source_doc_ids, questions, duration_minutes=20):
    create_table_quizzes()
    create_table_quiz_questions()

    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        source_json = json.dumps(source_doc_ids or [], ensure_ascii=False)
        so_cau = len(questions)
        cursor.execute(
            "INSERT INTO quizzes (tieu_de, mo_ta, so_cau, duration_minutes, source_documents) VALUES (%s, %s, %s, %s, %s)",
            (tieu_de, mo_ta, so_cau, duration_minutes, source_json)
        )
        id_quiz = cursor.lastrowid

        for q in questions:
            loai_quiz = (q.get("type") or q.get("loai") or "multiple_choice").strip()
            phan_loai = (q.get("section") or q.get("phan_loai") or "vocabulary").strip().lower()
            noi_dung = (q.get("question") or q.get("noi_dung") or "").strip()
            options = q.get("options") or []
            dap_an = q.get("answer")
            giai_thich = (q.get("explanation") or q.get("giai_thich") or "").strip()
            hint = (q.get("hint") or q.get("goi_y") or "").strip()

            if not noi_dung or dap_an is None:
                raise ValueError("Mỗi câu quiz phải có nội dung và đáp án")

            cursor.execute(
                "INSERT INTO quiz_questions (id_quiz, loai_quiz, phan_loai, noi_dung, options, dap_an, giai_thich, hint) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (id_quiz, loai_quiz, phan_loai, noi_dung, json.dumps(options, ensure_ascii=False), json.dumps(dap_an, ensure_ascii=False), giai_thich, hint)
            )

        connection.commit()
        return id_quiz
    except Exception as e:
        print("❌ Lỗi khi tạo quiz:", e)
        connection.rollback()
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_list():
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_quiz, tieu_de, mo_ta, so_cau, duration_minutes, ngay_tao FROM quizzes ORDER BY ngay_tao DESC"
        )
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi khi lấy danh sách quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_detail(id_quiz):
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_quiz, tieu_de, mo_ta, so_cau, duration_minutes, source_documents, ngay_tao FROM quizzes WHERE id_quiz = %s",
            (id_quiz,)
        )
        quiz = cursor.fetchone()
        if not quiz:
            return None

        cursor.execute(
            "SELECT id_question, loai_quiz, phan_loai, noi_dung, options, dap_an, giai_thich, hint FROM quiz_questions WHERE id_quiz = %s ORDER BY id_question",
            (id_quiz,)
        )
        questions = cursor.fetchall() or []

        for q in questions:
            try:
                q["options"] = json.loads(q["options"] or "[]")
            except Exception:
                q["options"] = []
            try:
                q["dap_an"] = json.loads(q["dap_an"] or "null")
            except Exception:
                q["dap_an"] = q.get("dap_an")

        quiz["questions"] = questions
        return quiz
    except Error as e:
        print("❌ Lỗi khi lấy chi tiết quiz:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def submit_quiz(id_nguoi_dung, id_quiz, bai_lam):
    create_table_quiz_results()
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_question, loai_quiz, phan_loai, noi_dung, options, dap_an FROM quiz_questions WHERE id_quiz = %s",
            (id_quiz,)
        )
        questions = cursor.fetchall() or []
        if not questions:
            print("⚠️ Không có quiz hoặc câu hỏi cho quiz này")
            return None

        question_map = {q["id_question"]: q for q in questions}
        detailed = []
        correct_count = 0
        total = len(questions)

        for item in bai_lam:
            qid = item.get("id_question")
            if qid not in question_map:
                continue

            q = question_map[qid]
            answer_data = q.get("dap_an")
            options = q.get("options") or []
            user_answer = item.get("dap_an_chon") if item.get("dap_an_chon") is not None else item.get("tra_loi")
            is_correct = False
            correct_value = answer_data
            user_value = user_answer

            def normalize(v):
                return str(v).strip().lower()

            if isinstance(options, list) and len(options) > 0 and user_answer is not None:
                selected_texts = []
                if isinstance(user_answer, list):
                    for selected in user_answer:
                        try:
                            idx = int(selected)
                            if 0 <= idx < len(options):
                                selected_texts.append(str(options[idx]))
                        except Exception:
                            selected_texts.append(str(selected))
                else:
                    try:
                        idx = int(user_answer)
                        if 0 <= idx < len(options):
                            selected_texts.append(str(options[idx]))
                        else:
                            selected_texts.append(str(user_answer))
                    except Exception:
                        selected_texts.append(str(user_answer))

                user_value = selected_texts if len(selected_texts) != 1 else selected_texts[0]

                if isinstance(answer_data, list):
                    normalized_user = sorted(normalize(x) for x in selected_texts)
                    normalized_answer = sorted(normalize(x) for x in answer_data)
                    is_correct = normalized_user == normalized_answer
                else:
                    normalized_correct = normalize(answer_data)
                    is_correct = any(normalize(x) == normalized_correct for x in selected_texts)
            else:
                if isinstance(answer_data, list):
                    normalized_user = [normalize(x) for x in (user_answer or [])]
                    normalized_answer = [normalize(x) for x in answer_data]
                    is_correct = sorted(normalized_user) == sorted(normalized_answer)
                else:
                    if user_answer is None:
                        user_value = ""
                    user_text = normalize(user_answer)
                    correct_text = normalize(answer_data)
                    is_correct = user_text == correct_text

            if is_correct:
                correct_count += 1

            detailed.append({
                "id_question": qid,
                "loai_quiz": q.get("loai_quiz"),
                "user_answer": user_value,
                "correct_answer": correct_value,
                "correct": is_correct
            })

        diem = round((correct_count / total) * 10, 2) if total else 0
        cursor.execute(
            "INSERT INTO quiz_results (id_nguoi_dung, id_quiz, diem, correct_count, total_questions, chi_tiet) VALUES (%s, %s, %s, %s, %s, %s)",
            (id_nguoi_dung, id_quiz, diem, correct_count, total, json.dumps(detailed, ensure_ascii=False))
        )
        connection.commit()

        passed = (correct_count / total) >= (2/3)
        reward = None
        message = ""
        streak_result = None

        if passed:
            streak_result = award_streak_points(id_nguoi_dung, points=10)
            if streak_result.get("reward_given"):
                reward = streak_result.get("reward") or []
                message = f"Chúc mừng! Bạn đã hoàn thành quiz và nhận {len(reward)} flashcard phần thưởng."
            else:
                message = f"Chúc mừng! Bạn đã hoàn thành quiz và nhận +10 điểm streak. Tổng điểm streak hiện tại: {streak_result.get('streak_points', 0)}."
        else:
            message = "Bạn hãy cố gắng lần sau nhé! Hãy xem lại bài và luyện thêm." 

        return {
            "status": passed and "passed" or "failed",
            "diem": diem,
            "correct_count": correct_count,
            "total_questions": total,
            "reward": reward,
            "message": message,
            "streak": streak_result,
            "chi_tiet": detailed
        }
    except Error as e:
        print("❌ Lỗi khi nộp quiz:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_history(id_nguoi_dung, limit=10):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_result, id_quiz, diem, correct_count, total_questions, chi_tiet, ngay_tao FROM quiz_results WHERE id_nguoi_dung = %s ORDER BY ngay_tao DESC LIMIT %s",
            (id_nguoi_dung, limit)
        )
        history = cursor.fetchall() or []
        for item in history:
            try:
                item["chi_tiet"] = json.loads(item["chi_tiet"] or "[]")
            except Exception:
                item["chi_tiet"] = []
        return history
    except Error as e:
        print("❌ Lỗi khi lấy lịch sử quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_question_by_id(question_id):
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_question, id_quiz, loai_quiz, phan_loai, noi_dung, options, dap_an, giai_thich, hint FROM quiz_questions WHERE id_question = %s",
            (question_id,)
        )
        result = cursor.fetchone()
        if result:
            try:
                result["options"] = json.loads(result["options"] or "[]")
            except Exception:
                result["options"] = []
            try:
                result["dap_an"] = json.loads(result["dap_an"] or "null")
            except Exception:
                result["dap_an"] = result.get("dap_an")
        return result
    except Error as e:
        print("❌ Lỗi khi lấy câu hỏi quiz:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_document(id_document):
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_document, tieu_de, noi_dung, ngay_tao FROM quiz_documents WHERE id_document = %s",
            (id_document,)
        )
        return cursor.fetchone()
    except Error as e:
        print("❌ Lỗi khi lấy tài liệu quiz:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_by_id(id_quiz):
    return get_quiz_detail(id_quiz)


def delete_quiz(id_quiz):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM quizzes WHERE id_quiz = %s", (id_quiz,))
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print("❌ Lỗi khi xóa quiz:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def delete_quiz_document(id_document):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM quiz_documents WHERE id_document = %s", (id_document,))
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        print("❌ Lỗi khi xóa tài liệu quiz:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_source_documents(id_quiz):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT source_documents FROM quizzes WHERE id_quiz = %s", (id_quiz,))
        row = cursor.fetchone()
        if not row:
            return []
        try:
            return json.loads(row["source_documents"] or "[]")
        except Exception:
            return []
    except Error as e:
        print("❌ Lỗi khi lấy source_documents quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quizzes_by_document(id_document):
    quizzes = get_quiz_list()
    return [q for q in quizzes if id_document in (json.loads(q.get("source_documents") or "[]") if q.get("source_documents") else [])]


def get_quiz_documents_for_dashboard(limit=20):
    return get_quiz_documents(limit)


def get_quiz_history_summary(id_nguoi_dung, limit=10):
    return get_quiz_history(id_nguoi_dung, limit)


def get_quiz_meta(id_quiz):
    return get_quiz_detail(id_quiz)


# ---------------- Moderation helpers ----------------
def record_infraction(user_id, reason, weight=1):
    """Record a simple infraction (used by anti-spam heuristics)."""
    conn = connect_to_mysql()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                id_infraction INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                reason VARCHAR(255),
                weight INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("INSERT INTO infractions (user_id, reason, weight) VALUES (%s,%s,%s)", (user_id, reason, weight))
        conn.commit()
        return True
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return False
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


def get_recent_infractions(user_id, minutes=60):
    conn = connect_to_mysql()
    if conn is None:
        return 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT SUM(weight) FROM infractions WHERE user_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)", (user_id, minutes))
        row = cur.fetchone()
        return int(row[0] or 0)
    except Exception:
        return 0
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


def apply_ban(user_id, level=1, days=1, reason=None):
    conn = connect_to_mysql()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        # calculate end_at
        end_at = None
        if days:
            cur.execute("SELECT DATE_ADD(NOW(), INTERVAL %s DAY)", (days,))
            end_at = cur.fetchone()[0]
        cur.execute("INSERT INTO bans (user_id, level, reason, start_at, end_at, active) VALUES (%s,%s,%s,NOW(),%s,1)", (user_id, level, reason, end_at))
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except:
            pass
        return False
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


def is_user_banned(user_id):
    conn = connect_to_mysql()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM bans WHERE user_id=%s AND active=1 AND (end_at IS NULL OR end_at > NOW())", (user_id,))
        row = cur.fetchone()
        return int(row[0] or 0) > 0
    except Exception:
        return False
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


def auto_escalate_bans(user_id):
    """Check recent infractions and apply ban levels based on thresholds."""
    # thresholds (example): >=20 -> level3 30 days, >=10 -> level2 7 days, >=5 -> level1 1 day
    score_24h = 0
    conn = connect_to_mysql()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT SUM(weight) FROM infractions WHERE user_id=%s AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)", (user_id,))
        row = cur.fetchone()
        score_24h = int(row[0] or 0)
        if score_24h >= 20:
            apply_ban(user_id, level=3, days=30, reason=f'Auto ban: {score_24h} infractions in 24h')
            return True
        if score_24h >= 10:
            apply_ban(user_id, level=2, days=7, reason=f'Auto ban: {score_24h} infractions in 24h')
            return True
        if score_24h >= 5:
            apply_ban(user_id, level=1, days=1, reason=f'Auto ban: {score_24h} infractions in 24h')
            return True
        return False
    except Exception:
        try:
            conn.rollback()
        except:
            pass
        return False
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass


def get_user_quiz_results(id_nguoi_dung, limit=10):
    return get_quiz_history(id_nguoi_dung, limit)


def get_all_quiz_results(limit=100):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quiz_results ORDER BY ngay_tao DESC LIMIT %s", (limit,))
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi khi lấy tất cả quiz results:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_recent_quiz_results(limit=10):
    return get_all_quiz_results(limit)


def get_recent_quiz_documents(limit=20):
    return get_quiz_documents(limit)


def get_recent_quizzes(limit=20):
    return get_quiz_list()[:limit]


def get_admin_quiz_overview(limit=20):
    return {
        "quizzes": get_quiz_list()[:limit],
        "documents": get_quiz_documents(limit)
    }


def get_quiz_results_for_quiz(id_quiz, limit=20):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id_result, r.id_nguoi_dung, u.ten_dang_nhap, r.diem, r.correct_count, r.total_questions, r.ngay_tao FROM quiz_results r JOIN nguoi_dung u ON r.id_nguoi_dung = u.id_nguoi_dung WHERE r.id_quiz = %s ORDER BY r.ngay_tao DESC LIMIT %s",
            (id_quiz, limit)
        )
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi khi lấy kết quả quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_results_for_user(id_nguoi_dung, limit=20):
    return get_quiz_history(id_nguoi_dung, limit)


def refresh_quiz_documents_cache():
    return get_quiz_documents()


def refresh_quiz_list_cache():
    return get_quiz_list()


def refresh_quiz_history(id_nguoi_dung, limit=10):
    return get_quiz_history(id_nguoi_dung, limit)


def get_quiz_list_for_user(id_nguoi_dung):
    return get_quiz_list()


def get_quiz_detail_for_user(id_quiz, id_nguoi_dung=None):
    return get_quiz_detail(id_quiz)


def get_document_list_for_quiz(id_quiz):
    doc_ids = get_quiz_source_documents(id_quiz)
    return [get_quiz_document(i) for i in doc_ids if get_quiz_document(i)]


def get_quiz_document_titles(id_quiz):
    return [d.get("tieu_de") for d in get_document_list_for_quiz(id_quiz) if d]


def get_quiz_sources(id_quiz):
    return get_document_list_for_quiz(id_quiz)


def get_quiz_documents_count():
    connection = connect_to_mysql()
    if connection is None:
        return 0

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM quiz_documents")
        return cursor.fetchone()[0]
    except Error as e:
        print("❌ Lỗi khi đếm tài liệu quiz:", e)
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quizzes_count():
    connection = connect_to_mysql()
    if connection is None:
        return 0

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM quizzes")
        return cursor.fetchone()[0]
    except Error as e:
        print("❌ Lỗi khi đếm quiz:", e)
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_results_count():
    connection = connect_to_mysql()
    if connection is None:
        return 0

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM quiz_results")
        return cursor.fetchone()[0]
    except Error as e:
        print("❌ Lỗi khi đếm kết quả quiz:", e)
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_summary():
    return {
        "documents": get_quiz_documents_count(),
        "quizzes": get_quizzes_count(),
        "results": get_quiz_results_count()
    }


def get_user_quiz_stats(id_nguoi_dung):
    return {
        "history": get_quiz_history(id_nguoi_dung, 10)
    }


def get_quiz_details_for_admin(id_quiz):
    return get_quiz_detail(id_quiz)


def get_quiz_documents_for_admin(limit=20):
    return get_quiz_documents(limit)


def get_available_quiz_docs():
    return get_quiz_documents()


def get_quiz_document_summaries(limit=20):
    docs = get_quiz_documents(limit)
    return [{"id_document": d.get("id_document"), "tieu_de": d.get("tieu_de"), "ngay_tao": d.get("ngay_tao")} for d in docs]


def get_quiz_list_summary(limit=20):
    return [{"id_quiz": q.get("id_quiz"), "tieu_de": q.get("tieu_de"), "so_cau": q.get("so_cau"), "ngay_tao": q.get("ngay_tao")} for q in get_quiz_list()[:limit]]


def get_quiz_list_for_admin(limit=20):
    return get_quiz_list_summary(limit)


def get_quiz_document_summary(id_document):
    doc = get_quiz_document(id_document)
    if not doc:
        return None
    return {"id_document": doc.get("id_document"), "tieu_de": doc.get("tieu_de"), "ngay_tao": doc.get("ngay_tao")}


def get_quiz_document_contents(limit=20):
    return get_quiz_documents(limit)


def get_quiz_document_data(id_document):
    return get_quiz_document(id_document)


def get_quiz_document_preview(id_document):
    doc = get_quiz_document(id_document)
    if not doc:
        return None
    return {"id_document": doc.get("id_document"), "tieu_de": doc.get("tieu_de"), "preview": (doc.get("noi_dung") or "")[:250]}


def get_quiz_docs_for_generator(limit=20):
    return get_quiz_documents(limit)


def get_quiz_detail_with_docs(id_quiz):
    quiz = get_quiz_detail(id_quiz)
    if not quiz:
        return None
    doc_ids = get_quiz_source_documents(id_quiz)
    quiz["documents"] = [get_quiz_document(i) for i in doc_ids if get_quiz_document(i)]
    return quiz


def get_quiz_overview_for_admin(limit=20):
    return {
        "documents": get_quiz_documents(limit),
        "quizzes": get_quiz_list()[:limit],
        "results": get_all_quiz_results(limit)
    }

def get_quiz_document_list_for_admin(limit=20):
    return get_quiz_documents(limit)

def get_quiz_list_for_dashboard(limit=20):
    return get_quiz_list()[:limit]

def get_quiz_document_dashboard(limit=20):
    return get_quiz_documents(limit)


def get_quiz_document_titles_for_admin(limit=20):
    return [d.get("tieu_de") for d in get_quiz_documents(limit)]

def get_quiz_documents_by_keyword(keyword, limit=20):
    connection = connect_to_mysql()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id_document, tieu_de, noi_dung, ngay_tao FROM quiz_documents WHERE LOWER(tieu_de) LIKE %s OR LOWER(noi_dung) LIKE %s ORDER BY ngay_tao DESC LIMIT %s", (f"%{keyword.lower()}%", f"%{keyword.lower()}%", limit))
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi tìm kiếm tài liệu quiz:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_recent_quiz_document_titles(limit=20):
    return [{"id_document": d.get("id_document"), "tieu_de": d.get("tieu_de")}
            for d in get_quiz_documents(limit)]

def get_recent_quiz_titles(limit=20):
    return [{"id_quiz": q.get("id_quiz"), "tieu_de": q.get("tieu_de"), "so_cau": q.get("so_cau")}
            for q in get_quiz_list()[:limit]]

def get_quiz_document_previews(limit=20):
    return [{"id_document": d.get("id_document"), "tieu_de": d.get("tieu_de"), "preview": (d.get("noi_dung") or "")[:180]} for d in get_quiz_documents(limit)]

def get_quiz_questions_for_quiz(id_quiz):
    quiz = get_quiz_detail(id_quiz)
    return quiz.get("questions", []) if quiz else []


def get_quiz_question_count(id_quiz):
    connection = connect_to_mysql()
    if connection is None:
        return 0
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM quiz_questions WHERE id_quiz = %s", (id_quiz,))
        return cursor.fetchone()[0]
    except Error as e:
        print("❌ Lỗi đếm câu hỏi quiz:", e)
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_document_count_by_keyword(keyword):
    return len(get_quiz_documents_by_keyword(keyword))

def search_quiz_documents(keyword, limit=20):
    return get_quiz_documents_by_keyword(keyword, limit)


def get_quiz_document_content_preview(id_document):
    return get_quiz_document_preview(id_document)


def get_quiz_document_titles_for_selection(limit=20):
    return get_quiz_document_titles(limit)


def get_quiz_document_details_for_selection(limit=20):
    return get_quiz_documents(limit)


def get_quiz_question_options(id_question):
    question = get_quiz_question_by_id(id_question)
    return question.get("options") if question else []


def get_quiz_question_answer(id_question):
    question = get_quiz_question_by_id(id_question)
    return question.get("dap_an") if question else None


def get_quiz_result_summary(id_result):
    connection = connect_to_mysql()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM quiz_results WHERE id_result = %s", (id_result,))
        return cursor.fetchone()
    except Error as e:
        print("❌ Lỗi lấy summary quiz result:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_results_for_recent_users(limit=20):
    return get_recent_quiz_results(limit)


def get_quiz_questions_for_recent_quizzes(limit=20):
    results = []
    quizzes = get_quiz_list()[:limit]
    for q in quizzes:
        results.append({"id_quiz": q.get("id_quiz"), "questions": get_quiz_questions_for_quiz(q.get("id_quiz"))})
    return results


def get_quiz_answer_for_question(question_id):
    return get_quiz_question_by_id(question_id)


def get_quiz_document_source_titles(id_quiz):
    return get_quiz_document_titles(id_quiz)


def get_quiz_documents_by_ids(ids):
    if not ids:
        return []
    try:
        ids = [int(i) for i in ids]
    except Exception:
        return []
    connection = connect_to_mysql()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        format_strings = ",".join(["%s"] * len(ids))
        cursor.execute(f"SELECT id_document, tieu_de, noi_dung, ngay_tao FROM quiz_documents WHERE id_document IN ({format_strings}) ORDER BY ngay_tao DESC", ids)
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi lấy quiz documents theo ids:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_quiz_documents_text_for_ids(ids):
    docs = get_quiz_documents_by_ids(ids)
    return "\n\n".join([f"{d.get('tieu_de')}: {d.get('noi_dung')}" for d in docs if d])


def get_quiz_documents_preview_text(limit=20):
    docs = get_quiz_documents(limit)
    return "\n\n".join([f"{d.get('tieu_de')}: {d.get('noi_dung')[:800]}" for d in docs if d])


def get_quiz_documents_for_generation(limit=10):
    return get_quiz_documents(limit)


def get_quiz_documents_for_admin_selection(limit=20):
    return get_quiz_documents(limit)


def get_quiz_documents_list_for_generation(limit=20):
    return get_quiz_documents(limit)


def get_quiz_prefetch_documents(limit=20):
    return get_quiz_documents(limit)


def get_quiz_document_corpus(limit=10):
    return get_quiz_documents(limit)


def get_reward_flashcard_list():
    return [
        {"en": "practice", "vn": "thực hành"},
        {"en": "vocabulary", "vn": "từ vựng"},
        {"en": "confidence", "vn": "tự tin"},
        {"en": "review", "vn": "ôn tập"},
        {"en": "progress", "vn": "tiến bộ"},
        {"en": "challenge", "vn": "thử thách"},
    ]


def has_user_received_flashcards_today(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM flashcard_rewards WHERE id_nguoi_dung = %s AND DATE(issued_at) = CURDATE()",
            (id_nguoi_dung,),
        )
        return cursor.fetchone()[0] > 0
    except Error as e:
        print("❌ Lỗi khi kiểm tra flashcard reward của user:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def insert_flashcard_reward(id_nguoi_dung, tu_vung, y_nghia, ly_do="Top 10 streak reward"):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO flashcard_rewards (id_nguoi_dung, tu_vung, y_nghia, ly_do) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (id_nguoi_dung, tu_vung, y_nghia, ly_do))
        connection.commit()
        return True
    except Error as e:
        print("❌ Lỗi khi lưu flashcard reward:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_user_flashcard_rewards(id_nguoi_dung, limit=20, offset=0):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_reward, tu_vung, y_nghia, ly_do, issued_at FROM flashcard_rewards "
            "WHERE id_nguoi_dung = %s ORDER BY issued_at DESC LIMIT %s OFFSET %s",
            (id_nguoi_dung, limit, offset),
        )
        return cursor.fetchall() or []
    except Error as e:
        print("❌ Lỗi khi lấy flashcard rewards của user:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def count_user_flashcard_rewards(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return 0

    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM flashcard_rewards WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,)
        )
        result = cursor.fetchone()
        return int(result[0]) if result else 0
    except Error as e:
        print("❌ Lỗi khi đếm flashcard rewards của user:", e)
        return 0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_user_email_by_id(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT email, ten_dang_nhap FROM nguoi_dung WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,),
        )
        return cursor.fetchone()
    except Error as e:
        print("❌ Lỗi khi lấy thông tin email user:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def reward_top_streak_users(limit=10):
    top_users = get_top_streak_users(limit)
    results = []
    all_flashcards = get_reward_flashcard_list()

    for user in top_users:
        user_id = user.get("id_nguoi_dung")
        if not user_id:
            continue

        if has_user_received_flashcards_today(user_id):
            results.append({"id_nguoi_dung": user_id, "already_sent": True})
            continue

        num_flashcards = random.randint(2, min(6, len(all_flashcards)))
        selected_flashcards = random.sample(all_flashcards, num_flashcards)

        saved = True
        for card in selected_flashcards:
            if not insert_flashcard_reward(user_id, card["en"], card["vn"]):
                saved = False

        user_info = get_user_email_by_id(user_id)
        if user_info and saved:
            results.append({"id_nguoi_dung": user_id, "sent_email": False, "count": num_flashcards})
        else:
            results.append({"id_nguoi_dung": user_id, "sent_email": False, "error": "Không tìm thấy email hoặc lưu thất bại"})

    return results


def update_user_streak_by_admin(id_nguoi_dung, new_streak_count):
    """Cập nhật streak_count của user bởi admin (cho phép chỉnh sửa thủ công)"""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE nguoi_dung SET streak_count = %s, last_streak_date = %s WHERE id_nguoi_dung = %s",
            (new_streak_count, date.today(), id_nguoi_dung),
        )
        connection.commit()
        print(f"✅ Admin cập nhật streak: user_id={id_nguoi_dung}, new_streak={new_streak_count}")
        return True
    except Error as e:
        print("❌ Lỗi khi cập nhật streak bởi admin:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def reset_user_streak(id_nguoi_dung):
    """Reset streak của user về 0"""
    return update_user_streak_by_admin(id_nguoi_dung, 0)


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
                audio_file VARCHAR(255) NULL,
                CONSTRAINT fk_ai_voice_user FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("SHOW COLUMNS FROM AI_voice LIKE 'audio_file'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE AI_voice ADD COLUMN audio_file VARCHAR(255) NULL")
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
                thoi_luong INT DEFAULT 60,
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            ALTER TABLE bai_kiem_tra
            ADD COLUMN IF NOT EXISTS thoi_luong INT DEFAULT 60;
        """)
        print("✅ Bảng `bai_kiem_tra` đã sẵn sàng!")
        
        # Tạo bảng cauhoi
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cauhoi (
                id_cauhoi INT AUTO_INCREMENT PRIMARY KEY,
                noi_dung LONGTEXT,
                loai_cau_hoi ENUM('trac_nghiem','tu_luan','sap_xep','dien_khuyet') DEFAULT 'trac_nghiem',
                muc_do ENUM('de','trung_binh','kho') DEFAULT 'de',
                phan_thi ENUM('listening','reading','writing','speaking') DEFAULT 'reading',
                ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_cap_nhat TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            ALTER TABLE cauhoi
            ADD COLUMN IF NOT EXISTS phan_thi ENUM('listening','reading','writing','speaking') DEFAULT 'reading';
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
                trang_thai ENUM('pending','completed') DEFAULT 'pending',
                ngay_nop TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ngay_lam TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
                FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            ALTER TABLE ket_qua_kiem_tra
            ADD COLUMN IF NOT EXISTS trang_thai ENUM('pending','completed') DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS ngay_nop TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
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


def get_user_planner(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        if conn is None:
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_planner (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL UNIQUE,
                planner JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        cursor.execute("SELECT planner FROM user_planner WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        row = cursor.fetchone()
        if row and row.get('planner') is not None:
            return {'planner': row['planner']}
        return None
    except Exception as e:
        print("❌ Lỗi get_user_planner:", e)
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def save_user_planner(id_nguoi_dung, planner):
    try:
        conn = connect_to_mysql()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_planner (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_nguoi_dung INT NOT NULL UNIQUE,
                planner JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        if planner is None:
            cursor.execute("DELETE FROM user_planner WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        else:
            payload = json.dumps(planner, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO user_planner (id_nguoi_dung, planner) VALUES (%s, %s) ON DUPLICATE KEY UPDATE planner=%s",
                (id_nguoi_dung, payload, payload)
            )
        conn.commit()
        return True
    except Exception as e:
        print("❌ Lỗi save_user_planner:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

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
        update_user_streak(id_nguoi_dung)
        award_streak_points(id_nguoi_dung, points=10)
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
def insert_ai_voice(id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai="gemini 2.0", audio_file=None):
    """Lưu hội thoại dạng giọng nói vào bảng AI_voice."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO AI_voice (id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai, audio_file)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai, audio_file))
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


def get_user_streak_info(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT streak_count, last_streak_date, streak_points, last_streak_action FROM nguoi_dung WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,),
        )
        user = cursor.fetchone()
        if not user:
            return None
        return {
            "streak_count": int(user.get("streak_count") or 0),
            "last_streak_date": user.get("last_streak_date"),
            "streak_points": int(user.get("streak_points") or 0),
            "last_streak_action": user.get("last_streak_action")
        }
    except Error as e:
        print("❌ Lỗi lấy thông tin streak user:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def award_streak_points(id_nguoi_dung, points=10, window_hours=5):
    connection = connect_to_mysql()
    if connection is None:
        return {"success": False, "streak_points": 0, "reward": None, "reward_given": False}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT streak_points, last_streak_action FROM nguoi_dung WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,),
        )
        user = cursor.fetchone()
        if not user:
            return {"success": False, "streak_points": 0, "reward": None, "reward_given": False}

        current_points = int(user.get("streak_points") or 0)
        last_action = user.get("last_streak_action")
        now = datetime.now()
        new_points = points

        if last_action and isinstance(last_action, datetime):
            elapsed = now - last_action
            if elapsed.total_seconds() <= window_hours * 3600:
                new_points = current_points + points

        reward = []
        reward_given = False
        if new_points >= 100:
            all_flashcards = get_reward_flashcard_list()
            while new_points >= 100 and all_flashcards:
                card = random.choice(all_flashcards)
                if insert_flashcard_reward(id_nguoi_dung, card["en"], card["vn"], "Streak point reward"):
                    reward.append(card)
                    reward_given = True
                new_points -= 100
            if not reward:
                reward = None

        update_cursor = connection.cursor()
        update_cursor.execute(
            "UPDATE nguoi_dung SET streak_points = %s, last_streak_action = %s WHERE id_nguoi_dung = %s",
            (new_points, now, id_nguoi_dung),
        )
        connection.commit()

        return {
            "success": True,
            "streak_points": new_points,
            "reward": reward,
            "reward_given": reward_given,
            "last_streak_action": now
        }
    except Error as e:
        print("❌ Lỗi khi cập nhật điểm streak:", e)
        return {"success": False, "streak_points": 0, "reward": None, "reward_given": False}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def increment_user_streak(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return {"success": False, "updated": False, "streak_count": 0}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT streak_count, last_streak_date FROM nguoi_dung WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,),
        )
        user = cursor.fetchone()
        if not user:
            return {"success": False, "updated": False, "streak_count": 0}

        today = date.today()
        current_streak = int(user.get("streak_count") or 0)
        last_date = user.get("last_streak_date")
        if last_date == today:
            return {"success": True, "updated": False, "streak_count": current_streak}

        if last_date == today - timedelta(days=1):
            new_streak = current_streak + 1
        else:
            new_streak = 1

        update_cursor = connection.cursor()
        update_cursor.execute(
            "UPDATE nguoi_dung SET streak_count = %s, last_streak_date = %s WHERE id_nguoi_dung = %s",
            (new_streak, today, id_nguoi_dung),
        )
        connection.commit()
        return {"success": True, "updated": True, "streak_count": new_streak}
    except Error as e:
        print("❌ Lỗi khi cập nhật streak:", e)
        return {"success": False, "updated": False, "streak_count": 0}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def update_user_streak(id_nguoi_dung):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT streak_count, last_streak_date FROM nguoi_dung WHERE id_nguoi_dung = %s",
            (id_nguoi_dung,),
        )
        user = cursor.fetchone()
        if not user:
            return False

        today = date.today()
        last_date = user.get("last_streak_date")

        if last_date == today:
            return True

        if last_date == today - timedelta(days=1):
            new_streak = int(user.get("streak_count") or 0) + 1
        else:
            new_streak = 1

        update_cursor = connection.cursor()
        update_cursor.execute(
            "UPDATE nguoi_dung SET streak_count = %s, last_streak_date = %s WHERE id_nguoi_dung = %s",
            (new_streak, today, id_nguoi_dung),
        )
        connection.commit()
        return True
    except Error as e:
        print("❌ Lỗi khi cập nhật streak:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_top_streak_users(limit=10):
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.id_nguoi_dung, u.ten_dang_nhap, u.streak_count, u.streak_points, u.last_streak_date,
                COALESCE((SELECT COUNT(*) FROM baihoc WHERE id_nguoi_dung = u.id_nguoi_dung), 0) AS total_baihoc
            FROM nguoi_dung u
            ORDER BY u.streak_points DESC, u.streak_count DESC, total_baihoc DESC, u.last_streak_action DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    except Error as e:
        print("❌ Lỗi khi lấy top streak users:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ///////////////////////////////// BÀI KIỂM TRA ///////////////////////////////////////////
def create_exam_db(tieu_de, mo_ta, cau_hoi_list, thoi_luong=60):
    # Đảm bảo các bảng tồn tại
    create_table_bai_kiem_tra()
    
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO bai_kiem_tra (tieu_de, mo_ta, thoi_luong) VALUES (%s, %s, %s)",
            (tieu_de, mo_ta, thoi_luong)
        )
        id_kt = cursor.lastrowid

        for q in cau_hoi_list:
            noi_dung = (q.get("noi_dung") or "").strip()
            loai = (q.get("loai_cau_hoi") or "").strip()
            muc_do = (q.get("muc_do") or "de").strip()
            phan_thi = (q.get("phan_thi") or "reading").strip().lower()
            dap_an = q.get("dap_an") or []

            if not noi_dung:
                raise ValueError("Câu hỏi thiếu nội dung")

            if loai not in ("trac_nghiem", "tu_luan"):
                raise ValueError("Loại câu hỏi không hợp lệ (chỉ trac_nghiem/tu_luan)")

            if phan_thi not in ("listening", "reading", "writing", "speaking"):
                phan_thi = "reading"

            cursor.execute(
                "INSERT INTO cauhoi (noi_dung, loai_cau_hoi, muc_do, phan_thi) VALUES (%s, %s, %s, %s)",
                (noi_dung, loai, muc_do, phan_thi)
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
            SELECT ch.id_cauhoi, ch.noi_dung, ch.loai_cau_hoi, ch.muc_do, ch.phan_thi
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

        chi_tiet = []
        for item in bai_lam:
            qid = item.get("id_cauhoi")
            if item.get("tra_loi_tu_luan") is not None:
                chi_tiet.append({
                    "id_cauhoi": qid,
                    "tra_loi_tu_luan": (item.get("tra_loi_tu_luan") or "").strip()
                })
            else:
                chi_tiet.append({
                    "id_cauhoi": qid,
                    "dap_an_chon": item.get("dap_an_da_chon", [])
                })

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO ket_qua_kiem_tra (id_nguoi_dung, id_kt, diem, chi_tiet, trang_thai, ngay_nop)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (id_nguoi_dung, id_kt, 0.0, json.dumps(chi_tiet, ensure_ascii=False), "pending"),
        )
        connection.commit()

        print(
            f"✅ Lưu bài làm kiểm tra: id_nguoi_dung={id_nguoi_dung}, id_kt={id_kt}, trạng thái=pending"
        )
        return {"status": "pending", "id_kt": id_kt, "tong_cau": len(cauhoi_ids), "chi_tiet": chi_tiet}
    except Error as e:
        print("❌ Lỗi khi chấm bài kiểm tra:", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def grade_pending_exams(id_nguoi_dung=None):
    """Chấm điểm các bài kiểm tra đang chờ nếu đã quá 15 phút."""
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT id_ket_qua, id_nguoi_dung, id_kt, chi_tiet
            FROM ket_qua_kiem_tra
            WHERE trang_thai = 'pending' AND ngay_nop <= NOW() - INTERVAL 15 MINUTE
        """
        params = []
        if id_nguoi_dung:
            sql += " AND id_nguoi_dung = %s"
            params.append(id_nguoi_dung)

        cursor.execute(sql, params)
        pending_results = cursor.fetchall() or []

        graded = []
        for row in pending_results:
            ket_qua_id = row["id_ket_qua"]
            user_id = row["id_nguoi_dung"]
            question_items = row["chi_tiet"]
            if isinstance(question_items, str):
                try:
                    question_items = json.loads(question_items)
                except Exception:
                    question_items = []

            question_ids = [item.get("id_cauhoi") for item in question_items if item.get("id_cauhoi")]
            if not question_ids:
                continue

            format_strings = ",".join(["%s"] * len(question_ids))
            cursor.execute(
                f"""
                SELECT ch.id_cauhoi, ch.loai_cau_hoi, da.id_dapan, da.noi_dung, da.ketqua
                FROM cauhoi ch
                LEFT JOIN dap_an da ON ch.id_cauhoi = da.id_cauhoi
                WHERE ch.id_cauhoi IN ({format_strings})
                """,
                question_ids,
            )

            correctness = {}
            for r in cursor.fetchall():
                qid = r.get("id_cauhoi")
                loai = (r.get("loai_cau_hoi") or "").lower()
                entry = correctness.setdefault(qid, {"loai": loai, "dap_an_tu_luan": None, "dap_an_trac_nghiem": set()})
                if loai == "tu_luan" and r.get("ketqua"):
                    entry["dap_an_tu_luan"] = (r.get("noi_dung") or "").strip()
                elif r.get("ketqua"):
                    entry["dap_an_trac_nghiem"].add(r.get("id_dapan"))

            correct_count = 0
            total = len(question_items)
            detailed = []
            for item in question_items:
                qid = item.get("id_cauhoi")
                info = correctness.get(qid, {})
                loai = (info.get("loai") or "").lower()

                if loai == "tu_luan":
                    user_answer = (item.get("tra_loi_tu_luan") or "").strip()
                    correct_text = (info.get("dap_an_tu_luan") or "").strip()
                    is_correct = bool(correct_text) and user_answer.lower() == correct_text.lower()
                    if is_correct:
                        correct_count += 1
                    detailed.append({
                        "id_cauhoi": qid,
                        "tra_loi_tu_luan": user_answer,
                        "dap_an_dung": correct_text,
                        "dung": is_correct,
                    })
                else:
                    selected = set(item.get("dap_an_chon") or item.get("dap_an_da_chon") or [])
                    correct_answers = info.get("dap_an_trac_nghiem", set())
                    is_correct = selected == correct_answers and len(correct_answers) > 0
                    if is_correct:
                        correct_count += 1
                    detailed.append({
                        "id_cauhoi": qid,
                        "dap_an_chon": list(selected),
                        "dap_an_dung": list(correct_answers),
                        "dung": is_correct,
                    })

            diem = round((correct_count / total) * 10, 2) if total else 0
            cursor.execute(
                """
                UPDATE ket_qua_kiem_tra
                SET diem = %s, chi_tiet = %s, trang_thai = 'completed'
                WHERE id_ket_qua = %s
                """,
                (diem, json.dumps(detailed, ensure_ascii=False), ket_qua_id),
            )
            connection.commit()
            award_streak_points(user_id, points=10)
            graded.append({"id_ket_qua": ket_qua_id, "diem": diem, "tong_cau": total, "so_cau_dung": correct_count})

        return graded
    except Error as e:
        print("❌ Lỗi khi chấm các bài pending:", e)
        return []
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


def get_ai_chat_history(id_nguoi_dung, limit=50):
    history = []
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, noi_dung_user, noi_dung_ai, model_ai, ngay_tao FROM AI_chat WHERE id_nguoi_dung=%s ORDER BY ngay_tao DESC LIMIT %s",
            (id_nguoi_dung, limit)
        )
        rows = cursor.fetchall() or []
        for row in rows:
            history.append({
                "id": row["id"],
                "user": row["noi_dung_user"],
                "ai": row["noi_dung_ai"],
                "model": row["model_ai"],
                "timestamp": row["ngay_tao"].strftime("%Y-%m-%d %H:%M:%S") if row.get("ngay_tao") else None
            })
    except Exception as e:
        print("❌ Lỗi lấy lịch sử AI_chat:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return history


def get_ai_voice_history(id_nguoi_dung, limit=50):
    history = []
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_chat AS id, tro_chuyen_user, tro_chuyen_ai, model_ai, audio_file, ngay_tao FROM AI_voice WHERE id_nguoi_dung=%s ORDER BY ngay_tao DESC LIMIT %s",
            (id_nguoi_dung, limit)
        )
        rows = cursor.fetchall() or []
        for row in rows:
            history.append({
                "id": row["id"],
                "user": row["tro_chuyen_user"],
                "ai": row["tro_chuyen_ai"],
                "model": row["model_ai"],
                "audio_file": row.get("audio_file"),
                "timestamp": row["ngay_tao"].strftime("%Y-%m-%d %H:%M:%S") if row.get("ngay_tao") else None
            })
    except Exception as e:
        print("❌ Lỗi lấy lịch sử AI_voice:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    return history


def delete_ai_chat_history(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM AI_chat WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        conn.commit()
        return True
    except Exception as e:
        print("❌ Lỗi xóa lịch sử AI_chat:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close(); conn.close()


def delete_ai_voice_history(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM AI_voice WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        conn.commit()
        return True
    except Exception as e:
        print("❌ Lỗi xóa lịch sử AI_voice:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close(); conn.close()


def save_ai_chat_history(id_nguoi_dung, entries):
    """Replace AI_chat history for a user with provided entries (list of {user, ai, model})."""
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        # delete existing
        cursor.execute("DELETE FROM AI_chat WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        # insert new entries (assume entries is list newest-first or oldest-first)
        if entries and isinstance(entries, list):
            for e in entries:
                user = e.get('user') or e.get('noi_dung_user') or ''
                ai = e.get('ai') or e.get('noi_dung_ai') or ''
                model = e.get('model') or 'gemini 2.0'
                cursor.execute("INSERT INTO AI_chat (id_nguoi_dung, noi_dung_user, noi_dung_ai, model_ai) VALUES (%s, %s, %s, %s)", (id_nguoi_dung, user, ai, model))
        conn.commit()
        return True
    except Exception as e:
        print("❌ Lỗi lưu lịch sử AI_chat:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close(); conn.close()


def save_ai_voice_history(id_nguoi_dung, entries):
    """Replace AI_voice history for a user with provided entries (list of {user, ai, model, audio_file})."""
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM AI_voice WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        if entries and isinstance(entries, list):
            for e in entries:
                user = e.get('user') or e.get('tro_chuyen_user') or ''
                ai = e.get('ai') or e.get('tro_chuyen_ai') or ''
                model = e.get('model') or 'gemini 2.0'
                audio_file = e.get('audio_file') or e.get('audio_url')
                if audio_file and audio_file.startswith('/static/audio/'):
                    audio_file = audio_file.split('/')[-1]
                cursor.execute("INSERT INTO AI_voice (id_nguoi_dung, tro_chuyen_user, tro_chuyen_ai, model_ai, audio_file) VALUES (%s, %s, %s, %s, %s)", (id_nguoi_dung, user, ai, model, audio_file))
        conn.commit()
        return True
    except Exception as e:
        print("❌ Lỗi lưu lịch sử AI_voice:", e)
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close(); conn.close()


def count_ai_chat_history(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM AI_chat WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        return cursor.fetchone()[0] or 0
    except Exception as e:
        print("❌ Lỗi đếm AI_chat:", e)
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def count_ai_voice_history(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM AI_voice WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        return cursor.fetchone()[0] or 0
    except Exception as e:
        print("❌ Lỗi đếm AI_voice:", e)
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def count_user_lessons(id_nguoi_dung):
    try:
        conn = connect_to_mysql()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM baihoc WHERE id_nguoi_dung=%s", (id_nguoi_dung,))
        return cursor.fetchone()[0] or 0
    except Exception as e:
        print("❌ Lỗi đếm bài học của user:", e)
        return 0
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


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