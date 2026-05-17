import smtplib
import ssl
import logging
import os
import time
from email.mime.text import MIMEText

SMTP_EMAIL = os.getenv('SMTP_EMAIL', '').strip()
SMTP_PASS = os.getenv('SMTP_PASS', '').strip()
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com').strip()
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'false').strip().lower() in ('1', 'true', 'yes', 'on')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT', '10'))
SMTP_RETRY_COUNT = int(os.getenv('SMTP_RETRY_COUNT', '3'))

# module logger - do not configure root logger here
logger = logging.getLogger(__name__)

def is_smtp_configured():
    return bool(SMTP_EMAIL and SMTP_PASS and SMTP_HOST and SMTP_PORT)


def _connect_smtp():
    if not is_smtp_configured():
        raise RuntimeError('SMTP configuration incomplete. Set SMTP_EMAIL, SMTP_PASS, SMTP_HOST, SMTP_PORT.')

    context = ssl.create_default_context()
    if SMTP_USE_SSL or SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT, context=context)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
        if SMTP_USE_TLS or SMTP_PORT in (587, 25):
            server.starttls(context=context)
    server.login(SMTP_EMAIL, SMTP_PASS)
    return server


def send_email(to_email, subject, body):
    if not is_smtp_configured():
        logger.error('SMTP not configured; cannot send email to %s', to_email)
        return False

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email

    for attempt in range(1, SMTP_RETRY_COUNT + 1):
        try:
            server = _connect_smtp()
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
            server.quit()
            logger.info('Email sent to %s (attempt %d)', to_email, attempt)
            return True
        except Exception as e:
            logger.exception('Error sending email to %s (attempt %d)', to_email, attempt)
            time.sleep(2 ** (attempt - 1))
    logger.error('Failed to send email to %s after %d attempts', to_email, SMTP_RETRY_COUNT)
    return False


def send_otp(to_email, otp):
    subject = "Mã xác thực đăng ký tài khoản"
    body = f"Mã OTP của bạn là: {otp}\nMã có hiệu lực trong 5 phút."
    return send_email(to_email, subject, body)


def send_flashcard_email(to_email, username, flashcards):
    subject = "Bạn được tặng flashcards từ vựng - Top 10 streak"
    lines = [
        f"Chào {username},",
        "",
        "Chúc mừng! Bạn đã nằm trong Top 10 người dùng có chuỗi học liên tiếp tốt nhất.",
        "Dưới đây là bộ flashcards từ vựng dành riêng cho bạn:",
        "",
    ]
    for item in flashcards:
        lines.append(f"- {item['en']} : {item['vn']}")
    lines.append("")
    lines.append("Hãy dùng chúng để ôn lại và tăng tốc tiến bộ tiếng Anh của bạn.")
    lines.append("Cảm ơn bạn đã học mỗi ngày cùng AI Learning Hub!")

    body = "\n".join(lines)
    return send_email(to_email, subject, body)


def send_admin_notification(to_email, subject, body):
    return send_email(to_email, subject, body)


def send_admin_webhook(webhook_url, payload):
    import json, requests, time
    if not webhook_url:
        return False
    headers = {'Content-Type': 'application/json'}
    for attempt in range(3):
        try:
            r = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=5)
            if 200 <= r.status_code < 300:
                logger.info("Webhook delivered to %s (status %s)", webhook_url, r.status_code)
                return True
            logger.warning("Webhook returned status %s: %s", r.status_code, r.text)
        except Exception as e:
            logger.exception("Error sending webhook to %s (attempt %d)", webhook_url, attempt + 1)
        time.sleep(2 ** attempt)
    logger.error("Failed to deliver webhook to %s after retries", webhook_url)
    return False


def make_slack_payload(text: str):
    return {"text": text}


def make_teams_payload(title: str, text: str):
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "title": title,
        "text": text,
    }


def send_slack_webhook(webhook_url, text: str):
    payload = make_slack_payload(text)
    return send_admin_webhook(webhook_url, payload)


def send_teams_webhook(webhook_url, title: str, text: str):
    payload = make_teams_payload(title, text)
    return send_admin_webhook(webhook_url, payload)
