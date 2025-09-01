from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash
import re

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

bp = Blueprint('users_modify_bp', __name__)

@bp.route('/modify', methods=['GET', 'POST'])
def modify():
    if 'user' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('users_login_bp.login'))

    userid = session['user']

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT userid, name, phone, DATE_FORMAT(birthdate, '%%Y-%%m-%%d') AS birthdate, email, password FROM users WHERE userid = %s"
            cursor.execute(sql, (userid,))
            user = cursor.fetchone()

            if not user:
                flash('사용자 정보를 찾을 수 없습니다.', 'error')
                return redirect(url_for('users_login_bp.login'))

            # --- POST: 회원정보 수정 처리 ---
            if request.method == 'POST':
                new_name = request.form['name'].strip()
                new_phone = request.form['phone'].strip()
                new_birthdate = request.form['birthdate'].strip()
                new_email = request.form['email'].strip()

                name_error = phone_error = birthdate_error = email_error = None
                current_password_error = new_password_error = confirm_password_error = None

                # 필수 입력값 체크
                if not all([new_name, new_phone, new_birthdate, new_email]):
                    if not new_name:
                        name_error = '이름은 필수 입력 사항입니다.'
                    if not new_phone:
                        phone_error = '전화번호는 필수 입력 사항입니다.'
                    if not new_birthdate:
                        birthdate_error = '생년월일은 필수 입력 사항입니다.'
                    if not new_email:
                        email_error = '이메일은 필수 입력 사항입니다.'
                    return render_template(
                        'modify.html', user=user,
                        name_error=name_error, phone_error=phone_error,
                        birthdate_error=birthdate_error, email_error=email_error,
                        password_fields_visible=False
                    )

                # 이메일 형식
                if not is_valid_email(new_email):
                    return render_template('modify.html', user=user, email_error="올바른 이메일 형식이 아닙니다.", password_fields_visible=False)

                # 이메일 중복 검사
                if new_email != user['email']:
                    cursor.execute("SELECT 1 FROM users WHERE email = %s", (new_email,))
                    if cursor.fetchone():
                        return render_template('modify.html', user=user, email_error="이미 사용 중인 이메일입니다.", password_fields_visible=False)

                # 생년월일 형식
                birthdate_clean = new_birthdate.replace('-', '').strip()
                if len(birthdate_clean) != 8 or not birthdate_clean.isdigit():
                    return render_template('modify.html', user=user, birthdate_error="생년월일 형식이 올바르지 않습니다 (YYYYMMDD 또는 YYYY-MM-DD 형식).", password_fields_visible=False)

                # ---- 비밀번호 변경 처리 ----
                current_password_input = request.form.get('current_password', '').strip()
                new_password_input = request.form.get('new_password', '').strip()
                confirm_password_input = request.form.get('confirm_password', '').strip()
                password_changed = False
                update_password_sql = ""
                update_password_param = ()
                # 비번 필드 열림 조건
                password_fields_visible = False

                if new_password_input:
                    password_fields_visible = True
                    # 1. 현재 비밀번호 미입력
                    if not current_password_input:
                        return render_template('modify.html', user=user,
                            current_password_error="새 비밀번호를 설정하려면 현재 비밀번호를 입력해야 합니다.",
                            password_fields_visible=True
                        )
                    # 2. 현재 비밀번호 불일치
                    if not check_password_hash(user['password'], current_password_input):
                        return render_template('modify.html', user=user,
                            current_password_error="현재 비밀번호가 일치하지 않습니다.",
                            password_fields_visible=True
                        )
                    # 3. 새 비밀번호 = 기존 비밀번호
                    if check_password_hash(user['password'], new_password_input):
                        return render_template('modify.html', user=user,
                            new_password_error="새 비밀번호가 기존 비밀번호와 동일합니다.",
                            password_fields_visible=True
                        )
                    # 4. 새 비번 = 확인 불일치
                    if new_password_input != confirm_password_input:
                        return render_template('modify.html', user=user,
                            confirm_password_error="새 비밀번호와 확인 비밀번호가 일치하지 않습니다.",
                            password_fields_visible=True
                        )
                    # 5. 새 비번 짧음
                    if len(new_password_input) < 6:
                        return render_template('modify.html', user=user,
                            new_password_error="새 비밀번호는 최소 6자 이상이어야 합니다.",
                            password_fields_visible=True
                        )

                    update_password_sql = ", password = %s"
                    hashed_new_password = generate_password_hash(new_password_input)
                    update_password_param = (hashed_new_password,)
                    password_changed = True

                # 최종 DB UPDATE
                sql = f"""
                UPDATE users
                SET name = %s, phone = %s, birthdate = %s, email = %s {update_password_sql}
                WHERE userid = %s
                """
                params = (new_name, new_phone, birthdate_clean, new_email) + update_password_param + (userid,)
                cursor.execute(sql, params)
                conn.commit()

                # 완료 메시지
                if password_changed:
                    flash('회원 정보 및 비밀번호가 성공적으로 수정되었습니다.', 'success')
                else:
                    flash('회원 정보가 성공적으로 수정되었습니다.', 'success')
                return redirect(url_for('users_profile_bp.profile'))

            # --- GET: 폼 출력 (에러 None 처리, 비번 필드 닫힘) ---
            return render_template(
                'modify.html', user=user,
                name_error=None, phone_error=None, birthdate_error=None, email_error=None,
                current_password_error=None, new_password_error=None, confirm_password_error=None,
                password_fields_visible=False
            )

    except Exception as e:
        current_app.logger.error(f"회원정보 수정 중 오류: {e}")
        flash('회원 정보 수정 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('users_profile_bp.profile'))
    finally:
        conn.close()
