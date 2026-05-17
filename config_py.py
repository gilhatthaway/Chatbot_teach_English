from save_mysql import *

# Khởi tạo database và bảng khi server start

def add_admin_first(ten_dang_nhap, email, mat_khau, vai_tro="admin"):
    connection = connect_to_mysql()
    if connection is None:
        return False, "[ERROR] Connection failed"

    try:
        cursor = connection.cursor()
        sql = """
            INSERT IGNORE INTO nguoi_dung (ten_dang_nhap, email, mat_khau, vai_tro)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (ten_dang_nhap, email, mat_khau, vai_tro))
        connection.commit()

        if cursor.rowcount == 0:
            return False, f"[WARN] User '{ten_dang_nhap}' or email '{email}' exists, skipped."
        else:
            return True, f"[OK] Added admin '{ten_dang_nhap}' successfully!"
    except Error as e:
        return False, f"[ERROR] Failed to add user: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def startup():
    create_database()
    create_table()
    create_baihoc_table()
    create_table_ai_voice()
    create_table_ai_chat()
    create_table_bai_kiem_tra()
    create_table_lich_su_chat()
    create_table_flashcard_rewards()
    create_table_quiz_documents()
    create_table_quizzes()
    create_table_quiz_questions()
    create_table_quiz_results()
    create_table_xac_thuc_email()
    create_table_otp_quen_mat_khau()
    add_admin_first("admin", "admin@gmail.com", "123")
    print("[OK] Database and tables initialized.")
    # show_all_users()

if __name__ == "__main__":
    startup()
