from save_mysql import *

# Khởi tạo database và bảng khi server start

def add_admin_first(ten_dang_nhap, email, mat_khau, vai_tro="admin"):
    connection = connect_to_mysql()
    if connection is None:
        return False, "❌ Lỗi kết nối CSDL"

    try:
        cursor = connection.cursor()
        sql = """
            INSERT IGNORE INTO nguoi_dung (ten_dang_nhap, email, mat_khau, vai_tro)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (ten_dang_nhap, email, mat_khau, vai_tro))
        connection.commit()

        if cursor.rowcount == 0:
            return False, f"⚠️ User '{ten_dang_nhap}' hoặc email '{email}' đã tồn tại, bỏ qua."
        else:
            return True, f"✅ Thêm admin '{ten_dang_nhap}' thành công!"
    except Error as e:
        return False, f"❌ Lỗi khi thêm user: {e}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Đã đóng kết nối MySQL.")

def startup():
    create_database()
    create_table()
    create_baihoc_table()
    create_table_ai_voice()
    create_table_ai_chat()
    create_table_bai_kiem_tra()
    add_admin_first("admin12", "admi22n@gmail.com", "admin123")
    print("✅ Database và bảng đã được khởi tạo, admin mặc định đã được thêm.")
    # show_all_users()

# startup()
