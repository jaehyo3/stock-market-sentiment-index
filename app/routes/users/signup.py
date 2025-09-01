from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_connection
from werkzeug.security import generate_password_hash
import re
import pymysql

bp = Blueprint('users_signup_bp', __name__)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        userid = request.form['userid'].strip()
        password = request.form['password'].strip()
        password2 = request.form.get('password2', '').strip()
        name = request.form['name'].strip()
        phone = request.form['phone'].strip().replace("-", "")
        birthdate = request.form['birthdate'].strip()
        email = request.form['email'].strip()
        agree_terms = request.form.get('agree_terms', '')

        form_data = request.form

        # 필수 입력 체크
        if not all([userid, password, password2, name, phone, birthdate, email]):
            errors['required'] = '모든 필드를 입력해주세요.'

        # 아이디 체크
        if not re.fullmatch(r'^[a-zA-Z0-9]{4,20}$', userid):
            errors['userid'] = '아이디는 영어와 숫자만 사용 가능하며, 4~20자여야 합니다.'

        # 비밀번호 체크
        if len(password) < 6:
            errors['password'] = '비밀번호는 최소 6자 이상이어야 합니다.'
        if password != password2:
            errors['password2'] = '비밀번호가 일치하지 않습니다.'

        # 이름: 한글 2자 이상
        if not re.fullmatch(r'^[가-힣]{2,}$', name):
            errors['name'] = "이름은 한글 2자 이상만 입력 가능합니다."

        # 생년월일 체크
        if len(birthdate) != 8 or not birthdate.isdigit():
            errors['birthdate'] = '생년월일 형식이 올바르지 않습니다 (YYYYMMDD 8자리 숫자).'

        # 전화번호: 010으로 시작 11자리
        if not re.fullmatch(r'^010\d{8}$', phone):
            errors['phone'] = '전화번호는 010으로 시작하는 11자리 숫자여야 합니다.'

        # 이메일 형식
        if not re.fullmatch(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z]+\.[a-zA-Z]+$', email):
            errors['email'] = '이메일 형식이 올바르지 않습니다.'

        # 약관 동의
        if not agree_terms:
            errors['terms'] = "이용약관에 동의해야 합니다."

        # (옵션) 이메일 차단 리스트
        block_list = ["bademail@example.com"]
        if email in block_list:
            errors['email'] = "이메일이 차단되어 있습니다."

        if errors:
            return render_template('signup.html', errors=errors, form=request.form)

        # --- DB 검사 (아이디/이메일 중복, 인증 여부) ---
        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # 아이디 중복
            cursor.execute("SELECT 1 FROM users WHERE userid=%s", (userid,))
            if cursor.fetchone():
                errors['userid'] = '이미 존재하는 아이디입니다.'
                cursor.close()
                conn.close()
                return render_template('signup.html', errors=errors, form=request.form)

            # 이메일 중복
            cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                errors['email'] = '이미 가입된 이메일입니다.'
                cursor.close()
                conn.close()
                return render_template('signup.html', errors=errors, form=request.form)

            # 이메일 인증 여부
            cursor.execute("""
                SELECT 1 FROM email_verification
                WHERE email=%s AND verified=1
                ORDER BY created_at DESC LIMIT 1
            """, (email,))
            result = cursor.fetchone()
            print("[디버그] 인증 쿼리 결과:", result)
            if not result:
                errors['email'] = '이메일 인증을 먼저 완료해주세요.'
                print("[디버그] 인증 실패로 회원가입 중단")
                cursor.close()
                conn.close()
                return render_template('signup.html', errors=errors, form=request.form)
            print("[디버그] 인증 성공, 회원가입 계속 진행")

            # INSERT
            birthdate_formatted = f"{birthdate[:4]}-{birthdate[4:6]}-{birthdate[6:]}"
            hashed_password = generate_password_hash(password)
            sql = """
                INSERT INTO users (userid, password, name, phone, birthdate, email)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (userid, hashed_password, name, phone, birthdate_formatted, email))
            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            errors['db'] = f'DB 저장 중 오류 발생: {e}'
            return render_template('signup.html', errors=errors, form=request.form)

        flash('회원가입이 성공적으로 완료되었습니다. 로그인해주세요!', 'success')
        return redirect(url_for('users_login_bp.login'))

    # GET 요청 시
    return render_template('signup.html', errors=errors, form=form_data)
