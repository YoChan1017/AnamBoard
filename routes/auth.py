from flask import (Blueprint, render_template, redirect, url_for,
                   request, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from db import query

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 9:
            flash('관리자 권한이 필요합니다.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ── 로그인 ────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = query(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,), one=True
        )
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['nickname'] = user['nickname']
            session['role']     = user['role']
            flash(f'{user["nickname"]}님 환영합니다!', 'success')
            return redirect(url_for('index'))
        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('auth/login.html')


# ── 로그아웃 ──────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))


# ── 회원가입 ──────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username   = request.form.get('username', '').strip()
        password   = request.form.get('password', '')
        password2  = request.form.get('password2', '')
        nickname   = request.form.get('nickname', '').strip()
        birth_date = request.form.get('birth_date') or None
        phone      = request.form.get('phone', '').strip() or None
        email      = request.form.get('email', '').strip() or None

        # ── 유효성 검사 ───────────────────────────────────────
        if not username or len(username) < 4:
            flash('아이디는 4자 이상이어야 합니다.', 'danger')
            return render_template('auth/register.html')
        if not password or len(password) < 6:
            flash('비밀번호는 6자 이상이어야 합니다.', 'danger')
            return render_template('auth/register.html')
        if password != password2:
            flash('비밀번호가 일치하지 않습니다.', 'danger')
            return render_template('auth/register.html')
        if not nickname:
            flash('닉네임을 입력해주세요.', 'danger')
            return render_template('auth/register.html')

        # ── 중복 체크 ─────────────────────────────────────────
        dup = query(
            "SELECT user_id FROM users WHERE username=%s OR nickname=%s OR (email=%s AND email IS NOT NULL)",
            (username, nickname, email), one=True
        )
        if dup:
            flash('이미 사용 중인 아이디, 닉네임 또는 이메일입니다.', 'danger')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password)
        query(
            """INSERT INTO users (username, password, nickname, birth_date, phone, email)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (username, hashed, nickname, birth_date, phone, email),
            commit=True
        )
        flash('회원가입이 완료되었습니다. 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
