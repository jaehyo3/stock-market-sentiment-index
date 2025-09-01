from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv

# [1] .env 경로: mail.py → services → app → Test(.env) : 3단계 상위
env_path = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    ), '.env'
)
print("찾으려는 .env 경로:", env_path)
load_dotenv(dotenv_path=env_path)

def send_verification_email(receiver, code):
    sender = os.getenv('GMAIL_EMAIL')
    password = os.getenv('GMAIL_APP_PASSWORD')
    print("GMAIL_EMAIL:", sender)
    print("GMAIL_APP_PASSWORD:", password)

    if not sender or not password:
        print("이메일 인증 환경변수(.env) 로딩 실패! 경로/값 다시 확인 필요.")
        return False

    msg = EmailMessage()
    msg['Subject'] = '[모아주식] 이메일 인증번호'
    msg['From'] = sender
    msg['To'] = receiver
    msg.set_content(f'인증번호는 [{code}] 입니다.\n5분 이내에 입력해주세요.')

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("이메일 발송 성공!")
        return True
    except Exception as e:
        print(f"메일 발송 오류: {e}")
        return False
