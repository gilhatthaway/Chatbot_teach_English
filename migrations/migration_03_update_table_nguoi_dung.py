from save_mysql import connect_to_mysql

def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    # ===================== thêm cột trang_thai_goi =====================
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME = 'nguoi_dung'
        AND COLUMN_NAME = 'trang_thai_goi'
    """)
    exists = cursor.fetchone()[0]

    if exists == 0:
        cursor.execute("""
            ALTER TABLE nguoi_dung
            ADD COLUMN trang_thai_goi ENUM('free','vip') DEFAULT 'free'
        """)
        print("✅ Added column trang_thai_goi")

    # ===================== thêm cột ngay_mua_goi_hoc =====================
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME = 'nguoi_dung'
        AND COLUMN_NAME = 'ngay_mua_goi_hoc'
    """)
    exists = cursor.fetchone()[0]

    if exists == 0:
        cursor.execute("""
            ALTER TABLE nguoi_dung
            ADD COLUMN ngay_mua_goi_hoc TIMESTAMP NULL
        """)
        print("✅ Added column ngay_mua_goi_hoc")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ UP 06_update_nguoi_dung completed successfully")


def down():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    # ===================== xóa cột ngay_mua_goi_hoc =====================
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME = 'nguoi_dung'
        AND COLUMN_NAME = 'ngay_mua_goi_hoc'
    """)
    exists = cursor.fetchone()[0]

    if exists == 1:
        cursor.execute("""
            ALTER TABLE nguoi_dung
            DROP COLUMN ngay_mua_goi_hoc
        """)
        print("✅ Dropped column ngay_mua_goi_hoc")

    # ===================== xóa cột trang_thai_goi =====================
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_NAME = 'nguoi_dung'
        AND COLUMN_NAME = 'trang_thai_goi'
    """)
    exists = cursor.fetchone()[0]

    if exists == 1:
        cursor.execute("""
            ALTER TABLE nguoi_dung
            DROP COLUMN trang_thai_goi
        """)
        print("✅ Dropped column trang_thai_goi")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ DOWN 06_update_nguoi_dung completed successfully")
