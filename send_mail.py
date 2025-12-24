import smtplib
from email.mime.text import MIMEText

SMTP_EMAIL = "viethoangtruong4703@gmail.com"
SMTP_PASS = "jlet ptyq kmzy ofia"  # mã 16 ký tự

def send_otp(to_email, otp):
    subject = "Mã xác thực đăng ký tài khoản"
    body = f"Mã OTP của bạn là: {otp}\nMã có hiệu lực trong 5 phút."

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SMTP_EMAIL, SMTP_PASS)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        print("✔ Email sent!")
        return True
    except Exception as e:
        print("❌ Error sending email:", e)
        return False
