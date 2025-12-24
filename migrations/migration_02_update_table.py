from save_mysql import connect_to_mysql

def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    # ===================== gói học =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goi_hoc (
        id_goi INT AUTO_INCREMENT PRIMARY KEY,
        ten_goi ENUM('free','vip') NOT NULL,
        gia INT DEFAULT 0,
        thoi_han_ngay INT NULL,
        gioi_han_bai_hoc_ngay INT NULL,
        gioi_han_bai_kiem_tra_ngay INT NULL,
        co_ai_voice TINYINT(1) DEFAULT 0,
        co_chat_khong_gioi_han TINYINT(1) DEFAULT 0
    )
    """)

    # ===================== chi tiết gói học =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chi_tiet_goi_hoc (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_nguoi_dung INT NOT NULL,
        id_goi INT NOT NULL,
        ngay_mua DATETIME DEFAULT CURRENT_TIMESTAMP,
        ngay_ket_thuc DATETIME NULL,
        phuong_thuc VARCHAR(50),
        trang_thai ENUM('active','expired','cancel') DEFAULT 'active',
        FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
        FOREIGN KEY (id_goi) REFERENCES goi_hoc(id_goi) ON DELETE CASCADE
    )
    """)

    # ===================== bài kiểm tra =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bai_kiem_tra (
        id_kt INT AUTO_INCREMENT PRIMARY KEY,
        tieu_de VARCHAR(255),
        mo_ta TEXT,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ngay_cap_nhat TIMESTAMP NULL
    )
    """)

    # ===================== câu hỏi =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cauhoi (
        id_cauhoi INT AUTO_INCREMENT PRIMARY KEY,
        noi_dung LONGTEXT,
        loai_cau_hoi ENUM('trac_nghiem','tu_luan','sap_xep','dien_khuyet'),
        muc_do ENUM('de','trung_binh','kho'),
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ngay_cap_nhat TIMESTAMP NULL
    )
    """)

    # ===================== liên kết bài kiểm tra - câu hỏi =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS baiKT_cauhoi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_kt INT NOT NULL,
        id_cauhoi INT NOT NULL,
        FOREIGN KEY (id_kt) REFERENCES bai_kiem_tra(id_kt) ON DELETE CASCADE,
        FOREIGN KEY (id_cauhoi) REFERENCES cauhoi(id_cauhoi) ON DELETE CASCADE
    )
    """)

    # ===================== đáp án =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dap_an (
        id_dapan INT AUTO_INCREMENT PRIMARY KEY,
        id_cauhoi INT NOT NULL,
        noi_dung VARCHAR(255),
        ketqua BOOLEAN,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ngay_cap_nhat TIMESTAMP NULL,
        FOREIGN KEY (id_cauhoi) REFERENCES cauhoi(id_cauhoi) ON DELETE CASCADE
    )
    """)

    # ===================== kết quả kiểm tra =====================
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
    )
    """)

    # ===================== lượt sử dụng =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS luot_su_dung (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_nguoi_dung INT NOT NULL,
        loai ENUM('baihoc','kiemtra','ai_voice'),
        ngay DATE,
        so_luot INT DEFAULT 0,
        FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
    )
    """)

    # ===================== đánh giá =====================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS danh_gia (
        id_danh_gia INT AUTO_INCREMENT PRIMARY KEY,
        id_nguoi_dung INT NOT NULL,
        loai ENUM('baihoc','kiemtra','chat'),
        so_sao INT,
        nhan_xet LONGTEXT,
        id_tham_chieu INT,
        ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Migration UP 05_full_schema thành công")


def down():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    tables = [
        "danh_gia",
        "luot_su_dung",
        "ket_qua_kiem_tra",
        "dap_an",
        "baiKT_cauhoi",
        "cauhoi",
        "bai_kiem_tra",
        "chi_tiet_goi_hoc",
        "goi_hoc"
    ]

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Migration DOWN 05_full_schema thành công")
