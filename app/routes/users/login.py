from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
import pymysql
from db import get_connection
from werkzeug.security import check_password_hash

bp = Blueprint('users_login_bp', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT userid, password, name, is_admin, is_active FROM users WHERE userid = %s"
                cursor.execute(sql, (userid,))
                user = cursor.fetchone()

            if user:
                if user.get('is_active') == 0:
                    flash('비활성화된 계정입니다. 로그인할 수 없습니다.', 'error')
                    return render_template('login.html', error=error_message)

                db_userid = user['userid']
                db_password_hash = user['password']
                db_name = user['name']
                db_is_admin = user.get('is_admin', False)  # 관리자 여부

                if check_password_hash(db_password_hash, password):
                    session.permanent = False
                    session['user'] = db_userid
                    session['name'] = db_name
                    session['is_admin'] = bool(db_is_admin)
                    flash('로그인 성공!', 'success')
                    return redirect(url_for('web_index_bp.index'))
                else:
                    flash('아이디 또는 비밀번호가 틀렸습니다.', 'error')
            else:
                flash('아이디 또는 비밀번호가 틀렸습니다.', 'error')
                
        except Exception as e:
            current_app.logger.error(f"로그인 오류: {e}")
            flash('로그인 처리 중 오류가 발생했습니다.', 'error')
        finally:
            conn.close()

    return render_template('login.html', error=error_message)
