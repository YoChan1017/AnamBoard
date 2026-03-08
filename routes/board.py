import os, uuid
from flask import (Blueprint, render_template, redirect, url_for,
                   request, session, flash, current_app, abort, send_file)
from werkzeug.utils import secure_filename
from db import query, get_db
from routes.auth import login_required

board_bp = Blueprint('board', __name__)


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def get_board_or_404(code):
    board = query("SELECT * FROM boards WHERE code=%s AND is_active=1", (code,), one=True)
    if not board:
        abort(404)
    return board


def can_read(board):
    return session.get('role', 0) >= board['read_role']


def can_write(board):
    if 'user_id' not in session:
        return False
    return session.get('role', 0) >= board['write_role']


# ── 게시판 목록 ───────────────────────────────────────────────
@board_bp.route('/board/<code>')
def list_posts(code):
    board = get_board_or_404(code)
    if not can_read(board):
        if 'user_id' not in session:
            flash('로그인이 필요한 서비스입니다.', 'warning')
            return redirect(url_for('auth.login'))
        else:
            flash('해당 게시판을 볼 권한이 없습니다.', 'danger')
            return redirect(url_for('index')) # 이미 로그인했는데 권한이 없는 경우만 홈으로

    page     = request.args.get('page', 1, type=int)
    keyword  = request.args.get('q', '').strip()
    per_page = current_app.config['POSTS_PER_PAGE']
    offset   = (page - 1) * per_page

    where  = "WHERE p.board_id=%s AND p.status='active'"
    params = [board['board_id']]

    if keyword:
        where += " AND (p.title LIKE %s OR p.content LIKE %s)"
        kw = f'%{keyword}%'
        params += [kw, kw]

    total = query(f"SELECT COUNT(*) as cnt FROM posts p {where}", params, one=True)['cnt']

    # 공지 먼저, 나머지는 최신순
    notices = query(
        f"SELECT p.*, u.nickname FROM posts p JOIN users u ON p.user_id=u.user_id "
        f"{where} AND p.is_notice=1 ORDER BY p.created_at DESC",
        params
    )
    posts = query(
        f"SELECT p.*, u.nickname FROM posts p JOIN users u ON p.user_id=u.user_id "
        f"{where} AND p.is_notice=0 ORDER BY p.created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template('board/list.html',
                           board=board, notices=notices, posts=posts,
                           page=page, total_pages=total_pages,
                           keyword=keyword, total=total)


# ── 글 보기 ───────────────────────────────────────────────────
@board_bp.route('/board/<code>/<int:post_id>')
def view_post(code, post_id):
    board = get_board_or_404(code)
    if not can_read(board):
        flash('열람 권한이 없습니다.', 'warning')
        return redirect(url_for('index'))

    post = query(
        "SELECT p.*, u.nickname FROM posts p JOIN users u ON p.user_id=u.user_id "
        "WHERE p.post_id=%s AND p.board_id=%s AND p.status='active'",
        (post_id, board['board_id']), one=True
    )
    if not post:
        abort(404)

    # 비밀글 접근 제한
    if post['is_secret']:
        uid  = session.get('user_id')
        role = session.get('role', 0)
        if uid != post['user_id'] and role < 9:
            flash('비밀글은 작성자와 관리자만 볼 수 있습니다.', 'warning')
            return redirect(url_for('board.list_posts', code=code))

    # 조회수 증가
    query("UPDATE posts SET view_count=view_count+1 WHERE post_id=%s", (post_id,), commit=True)

    comments = query(
        "SELECT c.*, u.nickname FROM comments c JOIN users u ON c.user_id=u.user_id "
        "WHERE c.post_id=%s ORDER BY c.created_at",
        (post_id,)
    )
    attachments = query("SELECT * FROM attachments WHERE post_id=%s", (post_id,))

    return render_template('board/view.html',
                           board=board, post=post,
                           comments=comments, attachments=attachments)


# ── 글 작성 ───────────────────────────────────────────────────
@board_bp.route('/board/<code>/write', methods=['GET', 'POST'])
@login_required
def write_post(code):
    board = get_board_or_404(code)
    if not can_write(board):
        flash('작성 권한이 없습니다.', 'warning')
        return redirect(url_for('board.list_posts', code=code))

    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        content   = request.form.get('content', '').strip()
        is_notice = bool(request.form.get('is_notice')) and session.get('role') == 9
        is_secret = bool(request.form.get('is_secret'))

        if not title or not content:
            flash('제목과 내용을 입력해주세요.', 'danger')
            return render_template('board/write.html', board=board)

        db  = get_db()
        cur = db.cursor()
        cur.execute(
            """INSERT INTO posts (board_id, user_id, title, content, is_notice, is_secret)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (board['board_id'], session['user_id'], title, content, is_notice, is_secret)
        )
        post_id = cur.lastrowid

        # ── 파일 첨부 ──────────────────────────────────────────
        files = request.files.getlist('attachments')
        for f in files:
            if f and f.filename and allowed_file(f.filename):
                orig     = secure_filename(f.filename)
                ext      = orig.rsplit('.', 1)[-1].lower() if '.' in orig else ''
                save_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_name)
                f.save(save_path)
                size = os.path.getsize(save_path)
                cur.execute(
                    """INSERT INTO attachments (post_id, origin_name, save_name, save_path, file_size, ext)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (post_id, orig, save_name, save_path, size, ext)
                )
        db.commit()
        flash('글이 등록되었습니다.', 'success')
        return redirect(url_for('board.view_post', code=code, post_id=post_id))

    return render_template('board/write.html', board=board)


# ── 글 수정 ───────────────────────────────────────────────────
@board_bp.route('/board/<code>/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(code, post_id):
    board = get_board_or_404(code)
    post  = query("SELECT * FROM posts WHERE post_id=%s AND status='active'",
                  (post_id,), one=True)
    if not post:
        abort(404)

    # 작성자 또는 관리자만 수정 가능
    if post['user_id'] != session['user_id'] and session.get('role') < 9:
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('board.view_post', code=code, post_id=post_id))

    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        content   = request.form.get('content', '').strip()
        is_notice = bool(request.form.get('is_notice')) and session.get('role') == 9
        is_secret = bool(request.form.get('is_secret'))

        if not title or not content:
            flash('제목과 내용을 입력해주세요.', 'danger')
            return render_template('board/write.html', board=board, post=post)

        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE posts SET title=%s, content=%s, is_notice=%s, is_secret=%s WHERE post_id=%s",
            (title, content, is_notice, is_secret, post_id)
        )

        # 새 첨부파일 추가
        files = request.files.getlist('attachments')
        for f in files:
            if f and f.filename and allowed_file(f.filename):
                orig      = secure_filename(f.filename)
                ext       = orig.rsplit('.', 1)[-1].lower() if '.' in orig else ''
                save_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], save_name)
                f.save(save_path)
                size = os.path.getsize(save_path)
                cur.execute(
                    """INSERT INTO attachments (post_id, origin_name, save_name, save_path, file_size, ext)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (post_id, orig, save_name, save_path, size, ext)
                )

        # 삭제 요청된 첨부파일 처리
        delete_ids = request.form.getlist('delete_file')
        for fid in delete_ids:
            att = query("SELECT * FROM attachments WHERE file_id=%s AND post_id=%s",
                        (fid, post_id), one=True)
            if att:
                try:
                    os.remove(att['save_path'])
                except OSError:
                    pass
                cur.execute("DELETE FROM attachments WHERE file_id=%s", (fid,))

        db.commit()
        flash('글이 수정되었습니다.', 'success')
        return redirect(url_for('board.view_post', code=code, post_id=post_id))

    attachments = query("SELECT * FROM attachments WHERE post_id=%s", (post_id,))
    return render_template('board/write.html', board=board, post=post, attachments=attachments)


# ── 글 삭제 ───────────────────────────────────────────────────
@board_bp.route('/board/<code>/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(code, post_id):
    post = query("SELECT * FROM posts WHERE post_id=%s AND status='active'",
                 (post_id,), one=True)
    if not post:
        abort(404)
    if post['user_id'] != session['user_id'] and session.get('role') < 9:
        flash('삭제 권한이 없습니다.', 'danger')
        return redirect(url_for('board.view_post', code=code, post_id=post_id))

    query("UPDATE posts SET status='deleted' WHERE post_id=%s", (post_id,), commit=True)
    flash('글이 삭제되었습니다.', 'success')
    return redirect(url_for('board.list_posts', code=code))


# ── 댓글 등록 ─────────────────────────────────────────────────
@board_bp.route('/board/<code>/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(code, post_id):
    content   = request.form.get('content', '').strip()
    is_secret = bool(request.form.get('is_secret'))
    if content:
        query(
            "INSERT INTO comments (post_id, user_id, content, is_secret) VALUES (%s,%s,%s,%s)",
            (post_id, session['user_id'], content, is_secret),
            commit=True
        )
        flash('댓글이 등록되었습니다.', 'success')
    return redirect(url_for('board.view_post', code=code, post_id=post_id))


# ── 댓글 삭제 ─────────────────────────────────────────────────
@board_bp.route('/board/<code>/<int:post_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(code, post_id, comment_id):
    c = query("SELECT * FROM comments WHERE comment_id=%s AND post_id=%s",
              (comment_id, post_id), one=True)
    if c and (c['user_id'] == session['user_id'] or session.get('role') == 9):
        query("UPDATE comments SET is_deleted=1 WHERE comment_id=%s", (comment_id,), commit=True)
        flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('board.view_post', code=code, post_id=post_id))


# ── 파일 다운로드 ─────────────────────────────────────────────
@board_bp.route('/download/<int:file_id>')
def download_file(file_id):
    att = query("SELECT * FROM attachments WHERE file_id=%s", (file_id,), one=True)
    if not att or not os.path.exists(att['save_path']):
        abort(404)
    return send_file(att['save_path'],
                     as_attachment=True,
                     download_name=att['origin_name'])
