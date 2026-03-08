import os
from flask import Flask, redirect, url_for, session, g
from config import Config
from db import init_app, query


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    init_app(app)

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth  import auth_bp
    from routes.board import board_bp
    from routes.admin import admin_bp
    from routes.user  import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp,  url_prefix='/user')

    # ── Context processor: 모든 템플릿에 boards, current_user 주입 ──
    @app.context_processor
    def inject_globals():
        boards = []
        current_user = None
        try:
            boards = query(
                "SELECT board_id, code, name, type FROM boards WHERE is_active=1 ORDER BY board_id",
            )
            if 'user_id' in session:
                current_user = query(
                    "SELECT user_id, username, nickname, role FROM users WHERE user_id=%s",
                    (session['user_id'],), one=True
                )
        except Exception:
            pass
        return dict(boards=boards, current_user=current_user)

    # ── Home ──────────────────────────────────────────────────
    @app.route('/')
    def index():
        try:
            first = query(
                "SELECT code FROM boards WHERE is_active=1 ORDER BY board_id LIMIT 1",
                one=True
            )
            if first:
                return redirect(url_for('board.list_posts', code=first['code']))
        except Exception:
            pass
        return redirect(url_for('auth.login'))

    return app


app = create_app()

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)
