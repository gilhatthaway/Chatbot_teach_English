import mysql.connector
from mysql.connector import Error

# Cấu hình
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "hoang123@"
DB_NAME = "aichat"

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


# Hàm tạo bảng nếu chưa có
# Hàm tạo bảng nếu chưa có (và thêm cột role nếu thiếu)
def create_table():
    """Tạo bảng users nếu chưa có, và thêm cột role nếu thiếu."""
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
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('user','admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Bảng `users` đã sẵn sàng!")

        # Kiểm tra xem cột role có tồn tại chưa
        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('user','admin') DEFAULT 'user'")
            print("🔧 Đã thêm cột `role` vào bảng `users`.")

    except Error as e:
        print("❌ Lỗi khi tạo bảng:", e)

# Hàm tạo bảng lessons
def create_lessons_table():
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
            CREATE TABLE IF NOT EXISTS lessons (
                id_lessons INT AUTO_INCREMENT PRIMARY KEY,
                id_user INT NOT NULL,
                topic VARCHAR(255) NOT NULL,
                model_ai VARCHAR(100) DEFAULT 'gemini 2.0',
                data_lesson LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ Bảng `lessons` đã sẵn sàng!")
    except Error as e:
        print("❌ Lỗi khi tạo bảng lessons:", e)
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
                id_user INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_AI VARCHAR(100) DEFAULT 'gemini 2.0',
                voice_user LONGTEXT,
                voice_ai LONGTEXT,
                CONSTRAINT fk_ai_voice_user FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
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
                id_user INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_AI VARCHAR(100) DEFAULT 'gemini 2.0',
                chat_user LONGTEXT,
                chat_ai LONGTEXT,
                CONSTRAINT fk_ai_chat_user FOREIGN KEY (id_user) REFERENCES users(id) ON DELETE CASCADE
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

# Hàm thêm user (mặc định role = user)
def insert_new_user(username, email, password):
    """Thêm user mới với role mặc định là 'user'."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, email, password, "user"))  # mặc định role = user
        connection.commit()
        print("✅ Thêm user mới thành công (role=user)!")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm user:", e)
        return False
        
# Hàm đăng nhập user
def login_user(email, password):
    """Kiểm tra email và password, role"""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dict thay vì tuple
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"
        cursor.execute(sql, (email, password))
        result = cursor.fetchone()
        if result:
            print(f"✅ Đăng nhập thành công! Xin chào {result['username']} (role={result['role']})")
        else:
            print("❌ Đăng nhập thất bại!")
        return result
    except Error as e:
        print("❌ Lỗi khi kiểm tra user:", e)
        return None

def insert_ai_lesson(id_user, topic, data_lesson, model_ai="gemini 2.0"):
    """ lưu lại bài học của user vào bảng lessons """
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO lessons (id_user, topic, model_ai, data_lesson)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_user, topic, model_ai, data_lesson))
        connection.commit()
        print(f"✅ Bài học mới đã được thêm cho user_id={id_user}, topic={topic}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm bài học:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Hàm thêm dữ liệu vào bảng AI_chat
def insert_ai_chat(id_user, chat_user, chat_ai, model_ai="gemini 2.0"):
    """Lưu hội thoại dạng text vào bảng AI_chat."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO AI_chat (id_user, chat_user, chat_ai, model_ai)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_user, chat_user, chat_ai, model_ai))
        connection.commit()
        print(f"✅ Hội thoại mới đã được thêm cho user_id={id_user}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm AI_chat:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# Hàm thêm dữ liệu vào bảng AI_voice
def insert_ai_voice(id_user, voice_user, voice_ai, model_ai="gemini 2.0"):
    """Lưu hội thoại dạng giọng nói vào bảng AI_voice."""
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO AI_voice (id_user, voice_user, voice_ai, model_ai)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (id_user, voice_user, voice_ai, model_ai))
        connection.commit()
        print(f"✅ Voice mới đã được thêm cho user_id={id_user}")
        return True
    except Error as e:
        print("❌ Lỗi khi thêm AI_voice:", e)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def count_all_user_lessons():
    """Trả về danh sách {id_user, total_lessons} của tất cả user"""
    connection = connect_to_mysql()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)  # dùng dictionary để dễ map JSON
        sql = """
            SELECT u.id AS id_user, u.username, COUNT(l.id_lessons) AS total_lessons
            FROM users u
            LEFT JOIN lessons l ON u.id = l.id_user
            GROUP BY u.id, u.username
            ORDER BY total_lessons DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        print("📊 Thống kê số topic của tất cả user:", results)
        return results
    except Error as e:
        print("❌ Lỗi khi thống kê bài học:", e)
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#//////////////////////////////////////////////////////////////// ADMIN    //////////////////////////////////////////////////////////////
 ## Thêm user mới với quyền admin.
def admin_insert_user(username, email, password, role):
    connection = connect_to_mysql()
    if connection is None:
        return False, "Lỗi kết nối CSDL"

    try:
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, email, password, role))
        connection.commit()
        return True, f"Thêm user '{username}' thành công (role={role})!"
    except Error as e:
        return False, f"Lỗi khi thêm user: {e}"

        
# Hàm update thông tin user
def update_user(user_id, username, email, password, role):
    connection = connect_to_mysql()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        sql = """
            UPDATE users
            SET username = %s, email = %s, password = %s, role = %s
            WHERE id = %s
        """
        cursor.execute(sql, (username, email, password, role, user_id))
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
        sql = "DELETE FROM users WHERE id = %s"
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


# Hàm xem toàn bộ người dùng trong bảng users
def show_all_users():
    """Lấy tất cả user trong bảng users."""
    connection = connect_to_mysql()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)  # trả về dạng dict
        cursor.execute("SELECT * FROM users")
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


# # Test
# if __name__ == "__main__":
#     create_database()   # 🔹 tạo DB nếu chưa có
#     # create_table()      # 🔹 tạo bảng nếu chưa có
#     # insert_new_user("bao", "bao123@gmail.com", "123")
#     # login_user("hoang123@gmail.com", "123456")
#     create_table_ai_voice() # tạo bảng AI_voice
#     create_table_ai_chat()  # tạo bảng AI_chat
#     create_lessons_table() # Tạo bảng lessons
#     # insert_lesson(3, "súng ống", "Nội dung bài học về súng ống ")
    
#     # # Thêm hội thoại text
#     # insert_ai_chat(3, "Hello AI!", "Xin chào, tôi là Hoang.")

#     # # Thêm hội thoại voice
#     # insert_ai_voice(3, "hi, i am Hoang", "voice_ai_data_base64_or_text")
#     # show_all_users()
#     total_topics = count_all_user_lessons()