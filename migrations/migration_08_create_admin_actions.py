from save_mysql import connect_to_mysql


def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()
    print("🚀 Migration UP 08: Create admin_actions audit table")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_actions (
            id_action INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT NULL,
            action_type VARCHAR(64) NOT NULL,
            target_type VARCHAR(64) NULL,
            target_id INT NULL,
            details LONGTEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')
    conn.commit()
    cursor.close(); conn.close()
    print('✅ Migration UP 08 completed')


def down():
    conn = connect_to_mysql(); cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS admin_actions")
    conn.commit(); cursor.close(); conn.close()
    print('✅ Migration DOWN 08 completed')


if __name__ == '__main__':
    up()
