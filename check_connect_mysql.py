import mysql.connector
from mysql.connector import Error

try:
    # Tạo kết nối
    connection = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="bao123",
    )

    if connection.is_connected():
        db_info = connection.get_server_info()
        print("✅ Kết nối MySQL thành công! Phiên bản:", db_info)

        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print("📂 Đang dùng database:", record)

except Error as e:
    print("❌ Lỗi kết nối MySQL:", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("🔌 Đã đóng kết nối MySQL.")
