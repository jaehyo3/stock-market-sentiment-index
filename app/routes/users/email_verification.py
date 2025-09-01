import random
import string
from flask import Blueprint, request, jsonify
from db import get_connection
from ...services.mail import send_verification_email
import pymysql

bp = Blueprint('email_verification', __name__)

# --- 1. 인증번호 발송 ---
@bp.route('/send_email_code', methods=['POST'])
def send_email_code():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'result': 'fail', 'msg': '이메일이 입력되지 않았습니다.'})

    # 6자리 인증번호 생성
    code = ''.join(random.choices(string.digits, k=6))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. 기존 인증 모두 무효화(verified=0)
        cursor.execute("UPDATE email_verification SET verified=0 WHERE email=%s", (email,))
        # 2. 새 인증번호 INSERT or UPDATE
        sql = """
            INSERT INTO email_verification (email, code, created_at, verified)
            VALUES (%s, %s, NOW(), 0)
            ON DUPLICATE KEY UPDATE code=%s, created_at=NOW(), verified=0
        """
        cursor.execute(sql, (email, code, code))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'result': 'fail', 'msg': f'DB 오류: {e}'})

    # 메일 발송
    try:
        send_verification_email(email, code)
    except Exception as e:
        return jsonify({'result': 'fail', 'msg': f'메일 발송 오류: {e}'})

    return jsonify({'result': 'success', 'msg': '인증번호가 발송되었습니다.'})

# --- 2. 인증번호 확인 ---
@bp.route('/verify_email_code', methods=['POST'])
def verify_email_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({'result': 'fail', 'message': '이메일과 인증번호를 모두 입력하세요.'})

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # 최근 인증번호 중 미인증(verified=0)만 검색
    sql = """
        SELECT code FROM email_verification
        WHERE email=%s AND verified=0
        ORDER BY created_at DESC LIMIT 1
    """
    cursor.execute(sql, (email,))
    row = cursor.fetchone()
    # fetchone()이 tuple일 수 있으니 아래처럼 처리!
    code_db = row['code'] if row else None
    if code_db and code_db == code:
        # 인증 성공 → 인증상태 변경
        update_sql = "UPDATE email_verification SET verified=1 WHERE email=%s AND code=%s"
        cursor.execute(update_sql, (email, code))
        conn.commit()
        result = {"result": "success", "message": "이메일 인증 성공!"}
    else:
        result = {"result": "fail", "message": "인증번호가 일치하지 않습니다."}
    cursor.close()
    conn.close()
    return jsonify(result)
