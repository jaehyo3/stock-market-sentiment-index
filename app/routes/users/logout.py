from flask import Blueprint, session, redirect, url_for

bp = Blueprint('users_logout_bp', __name__)

@bp.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('web_index_bp.index'))