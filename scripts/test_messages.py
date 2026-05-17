import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from save_mysql import connect_to_mysql
import requests
import sqlite3


def get_two_users():
    conn = connect_to_mysql()
    if conn is not None:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_nguoi_dung, ten_dang_nhap FROM nguoi_dung LIMIT 2")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows

    # Fallback to in-memory SQLite for local tests when MySQL unavailable
    sq = sqlite3.connect(':memory:')
    sq.row_factory = sqlite3.Row
    cur = sq.cursor()
    cur.execute('''
        CREATE TABLE nguoi_dung (
            id_nguoi_dung INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_dang_nhap TEXT,
            email TEXT
        )
    ''')
    cur.execute("INSERT INTO nguoi_dung (ten_dang_nhap, email) VALUES (?,?)", ('TestUser1','test1@example.com'))
    cur.execute("INSERT INTO nguoi_dang (ten_dang_nhap, email) VALUES (?,?)", ('TestUser2','test2@example.com'))
    sq.commit()
    cur.execute("SELECT id_nguoi_dung, ten_dang_nhap FROM nguoi_dung LIMIT 2")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close(); sq.close()
    return rows


if __name__ == '__main__':
    users = get_two_users()
    if len(users) < 2:
        print('Need at least 2 users in nguoi_dung table. Found:', users)
        raise SystemExit(1)
    u1 = users[0]['id_nguoi_dung']
    u2 = users[1]['id_nguoi_dung']
    print('Using users:', u1, users[0].get('ten_dang_nhap'), 'and', u2, users[1].get('ten_dang_nhap'))

    payload = {'sender_id': u1, 'receiver_id': u2, 'content': 'Automated test message'}
    try:
        r = requests.post('http://127.0.0.1:5000/api/messages/send', json=payload, timeout=5)
        print('POST /api/messages/send ->', r.status_code, r.text)
    except Exception as e:
        print('POST failed', e)

    try:
        r2 = requests.get(f'http://127.0.0.1:5000/api/messages/history?user_a={u1}&user_b={u2}', timeout=5)
        print('GET /api/messages/history ->', r2.status_code, r2.text[:1000])
    except Exception as e:
        print('GET history failed', e)
