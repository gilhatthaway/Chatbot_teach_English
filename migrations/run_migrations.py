import sys
import os
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIGRATIONS = [
    "migration_02_update_table",
    "migration_03_update_table_nguoi_dung",
    "migration_07_create_community_tables",
    "migration_08_create_admin_actions"
]

def run(direction="up"):
    print("\n==============================")
    print(f"🔥 Running migrations: {direction.upper()}")
    print("==============================\n")

    migrations = MIGRATIONS if direction == "up" else reversed(MIGRATIONS)

    for mig in migrations:
        try:
            module = importlib.import_module(mig)

            if not hasattr(module, direction):
                raise AttributeError(f"❌ {mig} thiếu hàm `{direction}()`")

            print(f"➡️  {direction.upper()} → {mig}")
            getattr(module, direction)()

        except Exception as e:
            print(f"❌ Lỗi khi chạy {mig}: {e}")
            sys.exit(1)

    print("\n✅ All migrations completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Thiếu tham số")
        print("👉 Dùng: python run_migrations.py up | down")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action not in ("up", "down"):
        print("❌ Tham số không hợp lệ (chỉ up | down)")
        sys.exit(1)

    run(action)
