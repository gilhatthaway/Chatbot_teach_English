from save_mysql import connect_to_mysql


def up():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    print("🚀 Migration UP 07: Create community, posts, comments, messaging and moderation tables")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communities (
            id_community INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description LONGTEXT,
            is_private TINYINT(1) DEFAULT 0,
            owner_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id_group INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description LONGTEXT,
            is_private TINYINT(1) DEFAULT 0,
            owner_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id_member INT AUTO_INCREMENT PRIMARY KEY,
            id_group INT NOT NULL,
            id_nguoi_dung INT NOT NULL,
            role ENUM('member','admin','owner') DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_group) REFERENCES groups(id_group) ON DELETE CASCADE,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id_post INT AUTO_INCREMENT PRIMARY KEY,
            id_nguoi_dung INT NOT NULL,
            id_community INT NULL,
            content LONGTEXT,
            media JSON NULL,
            is_deleted TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
            FOREIGN KEY (id_community) REFERENCES communities(id_community) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_reactions (
            id_reaction INT AUTO_INCREMENT PRIMARY KEY,
            id_post INT NOT NULL,
            id_nguoi_dung INT NOT NULL,
            reaction_type VARCHAR(64) DEFAULT 'like',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_post) REFERENCES posts(id_post) ON DELETE CASCADE,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id_comment INT AUTO_INCREMENT PRIMARY KEY,
            id_post INT NOT NULL,
            id_nguoi_dung INT NOT NULL,
            parent_comment_id INT NULL,
            content LONGTEXT,
            is_deleted TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            FOREIGN KEY (id_post) REFERENCES posts(id_post) ON DELETE CASCADE,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
            FOREIGN KEY (parent_comment_id) REFERENCES comments(id_comment) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment_reactions (
            id_reaction INT AUTO_INCREMENT PRIMARY KEY,
            id_comment INT NOT NULL,
            id_nguoi_dung INT NOT NULL,
            reaction_type VARCHAR(64) DEFAULT 'like',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_comment) REFERENCES comments(id_comment) ON DELETE CASCADE,
            FOREIGN KEY (id_nguoi_dung) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id_message INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NULL,
            group_id INT NULL,
            content LONGTEXT,
            attachments JSON NULL,
            is_deleted TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            edited_at TIMESTAMP NULL,
            FOREIGN KEY (sender_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id_group) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id_report INT AUTO_INCREMENT PRIMARY KEY,
            reporter_id INT NOT NULL,
            target_type ENUM('post','comment','message','user') NOT NULL,
            target_id INT NOT NULL,
            reason LONGTEXT,
            status ENUM('open','reviewing','resolved','dismissed') DEFAULT 'open',
            handled_by INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL,
            resolution LONGTEXT NULL,
            FOREIGN KEY (reporter_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
            FOREIGN KEY (handled_by) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            id_ban INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            level INT DEFAULT 1,
            reason LONGTEXT,
            start_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_at TIMESTAMP NULL,
            active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS infractions (
            id_infraction INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            reason VARCHAR(255),
            weight INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_points (
            id_point INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            points INT NOT NULL,
            reason VARCHAR(255),
            related_type VARCHAR(64),
            related_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id_call INT AUTO_INCREMENT PRIMARY KEY,
            caller_id INT NOT NULL,
            callee_id INT NULL,
            group_id INT NULL,
            status ENUM('ringing','in_progress','ended','missed') DEFAULT 'ringing',
            started_at TIMESTAMP NULL,
            ended_at TIMESTAMP NULL,
            recording_url VARCHAR(512) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (caller_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE CASCADE,
            FOREIGN KEY (callee_id) REFERENCES nguoi_dung(id_nguoi_dung) ON DELETE SET NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id_group) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stickers (
            id_sticker INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            url VARCHAR(512),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Migration UP 07 hoàn tất (bảng cộng đồng, bài viết, bình luận, tin nhắn, báo cáo, cấm)")


def down():
    conn = connect_to_mysql()
    cursor = conn.cursor()

    print("🔄 Migration DOWN 07: Drop community and messaging tables")

    tables = [
        'stickers','calls','activity_points','infractions','bans','reports','messages',
        'comment_reactions','comments','post_reactions','posts',
        'group_members','groups','communities'
    ]

    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t}")

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Migration DOWN 07 hoàn tất (đã xóa các bảng)")


if __name__ == '__main__':
    up()
