from flask import Blueprint, current_app, render_template, session, redirect, url_for, flash, request
from db import get_connection
from werkzeug.security import generate_password_hash

bp = Blueprint('users_admin_bp', __name__)

def admin_required():
    if 'user' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('users_login_bp.login'))
    if not session.get('is_admin'):
        flash('관리자 권한이 없습니다.', 'error')
        return redirect(url_for('web_index_bp.index'))
    return None

@bp.route('/admin')
def admin():
    auth_check = admin_required()
    if auth_check:
        return auth_check
    return render_template('admin.html')

@bp.route('/admin/users')
def user_list():
    auth_check = admin_required()
    if auth_check:
        return auth_check

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT userid, name, email, phone, birthdate, is_admin, is_active FROM users")
            users = cursor.fetchall()
        return render_template('admin_users.html', users=users)
    except Exception as e:
        current_app.logger.error(f"회원 목록 조회 오류: {e}")
        flash('회원 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('web_index_bp.index'))
    finally:
        conn.close()

# 회원 수정 (GET: 폼 표시, POST: 수정 처리)
@bp.route('/admin/users/edit/<userid>', methods=['GET', 'POST'])
def edit_user(userid):
    auth_check = admin_required()
    if auth_check:
        return auth_check

    conn = get_connection()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        birthdate = request.form.get('birthdate')
        is_admin = 1 if request.form.get('is_admin') == 'on' else 0
        password = request.form.get('password')

        try:
            with conn.cursor() as cursor:
                if password:
                    pw_hash = generate_password_hash(password)
                    sql = """
                        UPDATE users
                        SET name=%s, email=%s, phone=%s, birthdate=%s, is_admin=%s, password=%s
                        WHERE userid=%s
                    """
                    cursor.execute(sql, (name, email, phone, birthdate, is_admin, pw_hash, userid))
                else:
                    sql = """
                        UPDATE users
                        SET name=%s, email=%s, phone=%s, birthdate=%s, is_admin=%s
                        WHERE userid=%s
                    """
                    cursor.execute(sql, (name, email, phone, birthdate, is_admin, userid))
                conn.commit()
            flash('회원 정보가 수정되었습니다.', 'success')
            return redirect(url_for('users_admin_bp.user_list'))
        except Exception as e:
            current_app.logger.error(f"회원 수정 오류: {e}")
            flash('회원 정보를 수정하는 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('users_admin_bp.user_list'))
        finally:
            conn.close()

    else:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT userid, name, email, phone, birthdate, is_admin FROM users WHERE userid = %s", (userid,))
                user = cursor.fetchone()
            if not user:
                flash('해당 사용자를 찾을 수 없습니다.', 'error')
                return redirect(url_for('users_admin_bp.user_list'))
            return render_template('admin_edit_user.html', user=user)
        except Exception as e:
            current_app.logger.error(f"회원 조회 오류: {e}")
            flash('회원 정보를 불러오는 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('users_admin_bp.user_list'))
        finally:
            conn.close()

# 계정 비활성화
@bp.route('/admin/users/deactivate/<userid>', methods=['POST'])
def deactivate_user(userid):
    auth_check = admin_required()
    if auth_check:
        return auth_check

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET is_active = 0 WHERE userid = %s", (userid,))
            conn.commit()
        flash(f"{userid} 계정을 비활성화했습니다.", "success")
    except Exception as e:
        current_app.logger.error(f"비활성화 오류: {e}")
        flash('계정 비활성화 중 오류가 발생했습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('users_admin_bp.user_list'))


# 계정 활성화
@bp.route('/admin/users/activate/<userid>', methods=['POST'])
def activate_user(userid):
    auth_check = admin_required()
    if auth_check:
        return auth_check

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET is_active = 1 WHERE userid = %s", (userid,))
            conn.commit()
        flash(f"{userid} 계정을 다시 활성화했습니다.", "success")
    except Exception as e:
        current_app.logger.error(f"활성화 오류: {e}")
        flash('계정 활성화 중 오류가 발생했습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('users_admin_bp.user_list'))

# 회원 완전 삭제
@bp.route('/admin/users/delete/<userid>', methods=['POST'])
def delete_user(userid):
    auth_check = admin_required()
    if auth_check:
        return auth_check

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE userid = %s", (userid,))
            conn.commit()
        flash(f"{userid} 회원이 완전히 삭제되었습니다.", "success")
    except Exception as e:
        current_app.logger.error(f"회원 삭제 오류: {e}")
        flash('회원 삭제 중 오류가 발생했습니다.', 'error')
    finally:
        conn.close()
    return redirect(url_for('users_admin_bp.user_list'))
