from save_mysql import connect_to_mysql

def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    # ✅ tạo bảng nếu chưa có
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_quen_mat_khau (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(100) NOT NULL,
        otp VARCHAR(6) NOT NULL,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (email)
    )
    """)

    # ✅ kiểm tra cột đã tồn tại chưa
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME = 'otp_quen_mat_khau'
        AND COLUMN_NAME = 'id_nguoi_dung'
    """)
    exists = cursor.fetchone()[0]

    # ✅ chỉ thêm nếu chưa có
    if exists == 0:
        cursor.execute("""
            ALTER TABLE otp_quen_mat_khau
            ADD COLUMN id_nguoi_dung INT
        """)
        print("✅ Added column id_nguoi_dung")

    # ✅ xóa FK cũ nếu tồn tại
    cursor.execute("""
        SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_NAME='otp_quen_mat_khau'
        AND REFERENCED_TABLE_NAME='nguoi_dung'
    """)
    fk = cursor.fetchone()

    if fk:
        cursor.execute(f"""
            ALTER TABLE otp_quen_mat_khau
            DROP FOREIGN KEY {fk[0]}
        """)
        print("✅ Dropped old FK")

    # ✅ thêm FK mới
    cursor.execute("""
        ALTER TABLE otp_quen_mat_khau
        ADD CONSTRAINT fk_otp_quen_user
        FOREIGN KEY (id_nguoi_dung)
        REFERENCES nguoi_dung(id_nguoi_dung)
        ON DELETE CASCADE
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ UP completed successfully ✅")


def down():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    # ✅ xóa FK nếu tồn tại
    cursor.execute("""
        SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_NAME='otp_quen_mat_khau'
        AND REFERENCED_TABLE_NAME='nguoi_dung'
    """)
    fk = cursor.fetchone()

    if fk:
        cursor.execute(f"""
            ALTER TABLE otp_quen_mat_khau
            DROP FOREIGN KEY {fk[0]}
        """)
        print("✅ Removed FK")

    # ✅ xóa cột nếu tồn tại
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME='otp_quen_mat_khau'
        AND COLUMN_NAME='id_nguoi_dung'
    """)
    exists = cursor.fetchone()[0]

    if exists == 1:
        cursor.execute("""
            ALTER TABLE otp_quen_mat_khau
            DROP COLUMN id_nguoi_dung
        """)
        print("✅ Dropped column id_nguoi_dung")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ DOWN completed successfully ✅")
