import pymysql
from flask import g, current_app


def get_db():
    """요청마다 DB 연결을 g에 캐시하여 재사용."""
    if 'db' not in g:
        cfg = current_app.config
        kw = dict(
            host=cfg['MYSQL_HOST'],
            port=cfg['MYSQL_PORT'],
            user=cfg['MYSQL_USER'],
            password=cfg['MYSQL_PASSWORD'],
            database=cfg['MYSQL_DB'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        if cfg['MYSQL_SSL']:
            ssl_params = {'ssl': {}}
            if cfg.get('MYSQL_SSL_CA'):
                ssl_params['ssl']['ca'] = cfg['MYSQL_SSL_CA']
            kw.update(ssl_params)
        g.db = pymysql.connect(**kw)
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False, commit=False):
    """단일 SQL 실행 헬퍼."""
    db  = get_db()
    cur = db.cursor()
    cur.execute(sql, args)
    if commit:
        db.commit()
        return cur.lastrowid
    rv = cur.fetchone() if one else cur.fetchall()
    return rv


def init_app(app):
    app.teardown_appcontext(close_db)
