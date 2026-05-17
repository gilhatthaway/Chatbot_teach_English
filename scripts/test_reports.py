import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import requests
from save_mysql import connect_to_mysql


def send_report(reporter_id, target_type, target_id, reason='Test report'):
    try:
        r = requests.post('http://127.0.0.1:5000/api/report', json={
            'reporter_id': reporter_id,
            'target_type': target_type,
            'target_id': target_id,
            'reason': reason
        }, timeout=5)
        print('POST /api/report ->', r.status_code, r.text)
        return r.status_code == 200
    except Exception as e:
        print('Report POST failed', e)
        return False


def check_bans(user_id):
    conn = connect_to_mysql()
    if conn is None:
        print('DB unavailable')
        return None
    cur = conn.cursor()
    cur.execute('SELECT id_ban, user_id, level, reason, active, start_at, end_at FROM bans WHERE user_id=%s ORDER BY id_ban DESC LIMIT 5', (user_id,))
    rows = cur.fetchall()
    try:
        cur.close(); conn.close()
    except:
        pass
    return rows


if __name__ == '__main__':
    # Use reporter 1 reporting user 10
    reporter = 1
    target_user = 10
    print('Sending 5 reports for user', target_user)
    for i in range(5):
        ok = send_report(reporter, 'user', target_user, reason=f'Automated test {i+1}')
        time.sleep(0.5)

    print('Checking bans for user', target_user)
    bans = check_bans(target_user)
    print('Bans:', bans)
