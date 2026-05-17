import importlib
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

MIGRATIONS = [
    'migration_02_update_table',
    'migration_03_update_table_nguoi_dung',
    'migration_07_create_community_tables',
    'migration_08_create_admin_actions'
]

for m in MIGRATIONS:
    print(f"Running {m}...")
    try:
        mod = importlib.import_module('migrations.' + m)
        if hasattr(mod, 'up'):
            mod.up()
            print(f"{m} completed")
        else:
            print(f"{m} has no up() function")
    except Exception as e:
        print(f"Error running {m}: {e}")
        raise

print('All done')
