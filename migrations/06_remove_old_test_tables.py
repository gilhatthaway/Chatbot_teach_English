from save_mysql import connect_to_mysql


def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    print("🚀 Migration UP 06: Remove old test tables")

    # ❌ Xóa bảng chi tiết câu hỏi cũ
    cursor.execute("""
        DROP TABLE IF EXISTS chi_tiet_cau_hoi
    """)

    # ❌ Xóa bảng kết quả cũ
    cursor.execute("""
        DROP TABLE IF EXISTS ket_qua_nguoi_dung
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Migration UP 06 hoàn tất (đã xóa bảng cũ)")


def down():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    print("🔄 Migration DOWN 06: Restore old test tables")

    # 🔙 Khôi phục bảng chi_tiet_cau_hoi (cấu trúc cũ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_cau_hoi (
            id_cauhoi INT AUTO_INCREMENT PRIMARY KEY,
            id_kt INT NOT NULL,
            cau_hoi LONGTEXT,
            lua_chon JSON,
            dap_an VARCHAR(255),
            FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt)
                ON DELETE CASCADE
        )
    """)

    # 🔙 Khôi phục bảng ket_qua_nguoi_dung (cấu trúc cũ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ket_qua_nguoi_dung (
            id_ketqua INT AUTO_INCREMENT PRIMARY KEY,
            id_kt INT NOT NULL,
            id_nguoi_dung INT NOT NULL,
            diem FLOAT,
            chi_tiet JSON,
            ngay_lam TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt)
                ON DELETE CASCADE,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Migration DOWN 06 hoàn tất (đã khôi phục bảng cũ)")
if __name__ == "__main__":
    up()