from flask import (Blueprint, render_template, redirect, url_for,
                   request, session, flash)
from db import query
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__)


# ── 대시보드 ──────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'users':    query("SELECT COUNT(*) as c FROM users", one=True)['c'],
        'posts':    query("SELECT COUNT(*) as c FROM posts WHERE status='active'", one=True)['c'],
        'comments': query("SELECT COUNT(*) as c FROM comments WHERE is_deleted=0", one=True)['c'],
        'boards':   query("SELECT COUNT(*) as c FROM boards WHERE is_active=1", one=True)['c'],
    }
    recent_users  = query("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
    recent_posts  = query(
        "SELECT p.*, u.nickname, b.name as board_name "
        "FROM posts p JOIN users u ON p.user_id=u.user_id "
        "JOIN boards b ON p.board_id=b.board_id "
        "WHERE p.status='active' ORDER BY p.created_at DESC LIMIT 5"
    )
    return render_template('admin/dashboard.html',
                           stats=stats, recent_users=recent_users,
                           recent_posts=recent_posts)


# ── 사용자 목록 ───────────────────────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    keyword = request.args.get('q', '').strip()
    if keyword:
        user_list = query(
            "SELECT * FROM users WHERE username LIKE %s OR nickname LIKE %s ORDER BY created_at DESC",
            (f'%{keyword}%', f'%{keyword}%')
        )
    else:
        user_list = query("SELECT * FROM users ORDER BY created_at DESC")
    return render_template('admin/users.html', users=user_list, keyword=keyword)


# ── 사용자 수정 ───────────────────────────────────────────────
@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    user = query("SELECT * FROM users WHERE user_id=%s", (user_id,), one=True)
    if not user:
        flash('사용자를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        nickname  = request.form.get('nickname', '').strip()
        email     = request.form.get('email', '').strip() or None
        phone     = request.form.get('phone', '').strip() or None
        role      = int(request.form.get('role', 1))
        is_active = bool(request.form.get('is_active'))

        # 본인(슈퍼 관리자) 역할은 변경 불가
        if user_id == session['user_id'] and role != 9:
            flash('자신의 관리자 권한은 변경할 수 없습니다.', 'danger')
            return redirect(url_for('admin.user_edit', user_id=user_id))

        query(
            "UPDATE users SET nickname=%s, email=%s, phone=%s, role=%s, is_active=%s WHERE user_id=%s",
            (nickname, email, phone, role, is_active, user_id),
            commit=True
        )
        flash('사용자 정보가 수정되었습니다.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_edit.html', user=user)


# ── 사용자 활성/비활성 토글 ────────────────────────────────────
@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def user_toggle(user_id):
    if user_id == session['user_id']:
        flash('자기 자신의 계정은 비활성화할 수 없습니다.', 'danger')
        return redirect(url_for('admin.users'))
    query("UPDATE users SET is_active = NOT is_active WHERE user_id=%s",
          (user_id,), commit=True)
    flash('계정 상태가 변경되었습니다.', 'success')
    return redirect(url_for('admin.users'))


# ── 게시판 목록 ───────────────────────────────────────────────
@admin_bp.route('/boards')
@admin_required
def boards():
    board_list = query("SELECT * FROM boards ORDER BY board_id")
    return render_template('admin/boards.html', boards=board_list)


# ── 게시판 생성 ───────────────────────────────────────────────
@admin_bp.route('/boards/create', methods=['GET', 'POST'])
@admin_required
def board_create():
    if request.method == 'POST':
        code       = request.form.get('code', '').strip()
        name       = request.form.get('name', '').strip()
        btype      = request.form.get('type', 'NORMAL')
        read_role  = int(request.form.get('read_role', 1))
        write_role = int(request.form.get('write_role', 1))
        is_active  = bool(request.form.get('is_active'))

        if not code or not name:
            flash('코드와 이름을 입력해주세요.', 'danger')
            return render_template('admin/board_form.html')

        dup = query("SELECT board_id FROM boards WHERE code=%s", (code,), one=True)
        if dup:
            flash('이미 사용 중인 게시판 코드입니다.', 'danger')
            return render_template('admin/board_form.html')

        query(
            "INSERT INTO boards (code, name, type, read_role, write_role, is_active) VALUES (%s,%s,%s,%s,%s,%s)",
            (code, name, btype, read_role, write_role, is_active),
            commit=True
        )
        flash(f'게시판 [{name}]이 생성되었습니다.', 'success')
        return redirect(url_for('admin.boards'))

    return render_template('admin/board_form.html')


# ── 게시판 수정 ───────────────────────────────────────────────
@admin_bp.route('/boards/<int:board_id>/edit', methods=['GET', 'POST'])
@admin_required
def board_edit(board_id):
    board = query("SELECT * FROM boards WHERE board_id=%s", (board_id,), one=True)
    if not board:
        flash('게시판을 찾을 수 없습니다.', 'danger')
        return redirect(url_for('admin.boards'))

    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        btype      = request.form.get('type', 'NORMAL')
        read_role  = int(request.form.get('read_role', 1))
        write_role = int(request.form.get('write_role', 1))
        is_active  = bool(request.form.get('is_active'))

        query(
            "UPDATE boards SET name=%s, type=%s, read_role=%s, write_role=%s, is_active=%s WHERE board_id=%s",
            (name, btype, read_role, write_role, is_active, board_id),
            commit=True
        )
        flash('게시판이 수정되었습니다.', 'success')
        return redirect(url_for('admin.boards'))

    return render_template('admin/board_form.html', board=board)


# ── 게시판 삭제 ───────────────────────────────────────────────
@admin_bp.route('/boards/<int:board_id>/delete', methods=['POST'])
@admin_required
def board_delete(board_id):
    query("UPDATE boards SET is_active=0 WHERE board_id=%s", (board_id,), commit=True)
    flash('게시판이 비활성화되었습니다.', 'success')
    return redirect(url_for('admin.boards'))
