from flask import (Blueprint, render_template, redirect, url_for,
                   request, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from db import query
from routes.auth import login_required

user_bp = Blueprint('user', __name__)


# ── 내 정보 수정 ──────────────────────────────────────────────
@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = query("SELECT * FROM users WHERE user_id=%s", (session['user_id'],), one=True)

    if request.method == 'POST':
        nickname   = request.form.get('nickname', '').strip()
        email      = request.form.get('email', '').strip() or None
        phone      = request.form.get('phone', '').strip() or None
        birth_date = request.form.get('birth_date') or None
        cur_pw     = request.form.get('current_password', '')
        new_pw     = request.form.get('new_password', '')
        new_pw2    = request.form.get('new_password2', '')

        if not nickname:
            flash('닉네임을 입력해주세요.', 'danger')
            return render_template('user/profile.html', user=user)

        # 닉네임/이메일 중복 체크 (본인 제외)
        dup = query(
            "SELECT user_id FROM users WHERE (nickname=%s OR (email=%s AND email IS NOT NULL)) AND user_id != %s",
            (nickname, email, session['user_id']), one=True
        )
        if dup:
            flash('이미 사용 중인 닉네임 또는 이메일입니다.', 'danger')
            return render_template('user/profile.html', user=user)

        # 비밀번호 변경 요청 시
        if new_pw:
            if not check_password_hash(user['password'], cur_pw):
                flash('현재 비밀번호가 올바르지 않습니다.', 'danger')
                return render_template('user/profile.html', user=user)
            if len(new_pw) < 6:
                flash('새 비밀번호는 6자 이상이어야 합니다.', 'danger')
                return render_template('user/profile.html', user=user)
            if new_pw != new_pw2:
                flash('새 비밀번호가 일치하지 않습니다.', 'danger')
                return render_template('user/profile.html', user=user)
            query(
                "UPDATE users SET nickname=%s, email=%s, phone=%s, birth_date=%s, password=%s WHERE user_id=%s",
                (nickname, email, phone, birth_date, generate_password_hash(new_pw), session['user_id']),
                commit=True
            )
        else:
            query(
                "UPDATE users SET nickname=%s, email=%s, phone=%s, birth_date=%s WHERE user_id=%s",
                (nickname, email, phone, birth_date, session['user_id']),
                commit=True
            )

        session['nickname'] = nickname
        flash('내 정보가 업데이트되었습니다.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=user)


# ── 내가 쓴 글 ────────────────────────────────────────────────
@user_bp.route('/my-posts')
@login_required
def my_posts():
    page     = request.args.get('page', 1, type=int)
    per_page = 10
    offset   = (page - 1) * per_page

    total = query(
        "SELECT COUNT(*) as c FROM posts WHERE user_id=%s AND status='active'",
        (session['user_id'],), one=True
    )['c']

    posts = query(
        """SELECT p.*, b.name as board_name, b.code as board_code
           FROM posts p JOIN boards b ON p.board_id=b.board_id
           WHERE p.user_id=%s AND p.status='active'
           ORDER BY p.created_at DESC LIMIT %s OFFSET %s""",
        (session['user_id'], per_page, offset)
    )
    total_pages = (total + per_page - 1) // per_page
    return render_template('user/my_posts.html',
                           posts=posts, page=page, total_pages=total_pages, total=total)


# ── 내 글 삭제 ────────────────────────────────────────────────
@user_bp.route('/my-posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_my_post(post_id):
    post = query("SELECT * FROM posts WHERE post_id=%s AND user_id=%s AND status='active'",
                 (post_id, session['user_id']), one=True)
    if post:
        query("UPDATE posts SET status='deleted' WHERE post_id=%s", (post_id,), commit=True)
        flash('글이 삭제되었습니다.', 'success')
    return redirect(url_for('user.my_posts'))
