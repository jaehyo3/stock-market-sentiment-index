from flask import Blueprint, render_template, session, redirect, url_for, flash, current_app
import pandas as pd
import os
from db import get_connection


bp = Blueprint('users_profile_bp', __name__)


@bp.route('/profile')
def profile():
    if 'user' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('users_login_bp.login'))

    userid = session['user']

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT userid, name, phone, birthdate, email
            FROM users
            WHERE userid = %s
            """
            cursor.execute(sql, (userid,))
            user = cursor.fetchone()

        if not user:
            flash('사용자 정보를 찾을 수 없습니다.', 'error')
            return redirect(url_for('users_login_bp.login'))

        # 전화번호 포맷 변환
        phone = user.get('phone', '')
        if len(phone) == 11:
            user['phone'] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        elif len(phone) == 10:
            user['phone'] = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"

        return render_template('profile.html', user=user)

    except Exception as e:
        current_app.logger.error(f"프로필 조회 중 오류: {e}")
        flash('사용자 정보를 가져오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('users_login_bp.login'))
    finally:
        conn.close()
