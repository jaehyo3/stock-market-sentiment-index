from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
import pandas as pd
import os
from db import get_connection

bp = Blueprint('users_signout_bp', __name__)

@bp.route('/signout', methods=['GET', 'POST'])
def signout():
    if 'user' not in session:
        return redirect(url_for('users_login_bp.login'))

    if request.method == 'POST':
        userid = session['user']

        # ✅ MySQL DB에서 삭제 대신 비활성화 처리
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET is_active = 0 WHERE userid = %s", (userid,))
            conn.commit()

        except Exception as e:
            current_app.logger.error(f"DB 회원탈퇴(비활성화) 오류: {e}")
        finally:
            if conn:
                conn.close()

        # 세션 해제 후 메인으로 이동
        session.pop('user', None)
        session.pop('name', None)
        session.pop('is_admin', None)
        return redirect(url_for('web_index_bp.index'))
    
    return render_template('signout.html')