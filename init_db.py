"""
초기화 스크립트
1. 테이블 존재 여부 확인 후 없으면 CREATE
2. 기본 게시판 3개 생성 (공지사항, 자유게시판, 질문&건의사항)
3. 관리자 계정 생성

사용법:
  python init_db.py
"""
import os
import pymysql
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

# ── 테이블 DDL ────────────────────────────────────────────────
CREATE_TABLES = [
    (
        "users",
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id    INT AUTO_INCREMENT PRIMARY KEY,
            username   VARCHAR(30) BINARY NOT NULL UNIQUE,
            password   VARCHAR(255) NOT NULL,
            nickname   VARCHAR(30) NOT NULL UNIQUE,
            birth_date DATE,
            phone      VARCHAR(20),
            email      VARCHAR(100) UNIQUE,
            role       TINYINT DEFAULT 1,
            is_active  BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ),
    (
        "boards",
        """
        CREATE TABLE IF NOT EXISTS boards (
            board_id   INT AUTO_INCREMENT PRIMARY KEY,
            code       VARCHAR(30) NOT NULL UNIQUE,
            name       VARCHAR(50) NOT NULL,
            type       VARCHAR(20) DEFAULT 'NORMAL',
            read_role  TINYINT DEFAULT 1,
            write_role TINYINT DEFAULT 1,
            is_active  BOOLEAN DEFAULT TRUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ),
    (
        "posts",
        """
        CREATE TABLE IF NOT EXISTS posts (
            post_id    INT AUTO_INCREMENT PRIMARY KEY,
            board_id   INT NOT NULL,
            user_id    INT NOT NULL,
            title      VARCHAR(200) NOT NULL,
            content    MEDIUMTEXT NOT NULL,
            view_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_notice  BOOLEAN DEFAULT FALSE,
            is_secret  BOOLEAN DEFAULT FALSE,
            status     VARCHAR(20) DEFAULT 'active',
            FOREIGN KEY (board_id) REFERENCES boards(board_id),
            FOREIGN KEY (user_id)  REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ),
    (
        "comments",
        """
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INT AUTO_INCREMENT PRIMARY KEY,
            post_id    INT NOT NULL,
            user_id    INT NOT NULL,
            content    VARCHAR(1000) NOT NULL,
            is_secret  BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id)  REFERENCES posts(post_id),
            FOREIGN KEY (user_id)  REFERENCES users(user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ),
    (
        "attachments",
        """
        CREATE TABLE IF NOT EXISTS attachments (
            file_id     INT AUTO_INCREMENT PRIMARY KEY,
            post_id     INT NOT NULL,
            origin_name VARCHAR(255) NOT NULL,
            save_name   VARCHAR(255) NOT NULL,
            save_path   VARCHAR(255) NOT NULL,
            file_size   BIGINT NOT NULL,
            ext         VARCHAR(10),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ),
]


def get_conn():
    kw = dict(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DB', 'anam'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    if os.getenv('MYSQL_SSL', 'false').lower() == 'true':
        ssl_params = {'ssl': {}}
        ca = os.getenv('MYSQL_SSL_CA')
        if ca:
            ssl_params['ssl']['ca'] = ca
        kw.update(ssl_params)
    return pymysql.connect(**kw)


def create_tables(conn):
    """테이블이 없으면 생성."""
    cur = conn.cursor()
    print("📋 테이블 확인 중...")
    for table_name, ddl in CREATE_TABLES:
        cur.execute(
            "SELECT COUNT(*) as cnt FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s",
            (table_name,)
        )
        exists = cur.fetchone()['cnt'] > 0
        if exists:
            print(f"  [이미 존재] 테이블: {table_name}")
        else:
            cur.execute(ddl)
            conn.commit()
            print(f"  [테이블 생성] {table_name}")


def create_boards(conn):
    """기본 게시판 3개 삽입."""
    cur = conn.cursor()
    print("\n📌 기본 게시판 확인 중...")
    boards = [
        ('notice', '공지사항',      'NOTICE', 1, 9),  # 쓰기: 관리자 전용
        ('free',   '자유게시판',    'NORMAL', 1, 1),
        ('qna',    '질문&건의사항', 'NORMAL', 1, 1),
    ]
    for code, name, btype, read_role, write_role in boards:
        cur.execute("SELECT board_id FROM boards WHERE code=%s", (code,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO boards (code, name, type, read_role, write_role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (code, name, btype, read_role, write_role)
            )
            print(f"  [게시판 생성] {name} ({code})")
        else:
            print(f"  [이미 존재] 게시판: {code}")
    conn.commit()


def create_admin(conn):
    """관리자 계정 삽입."""
    cur = conn.cursor()
    print("\n👤 관리자 계정 확인 중...")
    admin_id   = os.getenv('ADMIN_USERNAME', 'admin')
    admin_pw   = os.getenv('ADMIN_PASSWORD', 'admin1234')
    admin_nick = os.getenv('ADMIN_NICKNAME', '관리자')

    cur.execute("SELECT user_id FROM users WHERE username=%s", (admin_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password, nickname, role) VALUES (%s, %s, %s, 9)",
            (admin_id, generate_password_hash(admin_pw), admin_nick)
        )
        conn.commit()
        print(f"  [관리자 생성] username={admin_id}  password={admin_pw}")
        print(f"  ⚠️  로그인 후 반드시 비밀번호를 변경하세요!")
    else:
        print(f"  [이미 존재] 관리자 계정: {admin_id}")


def init():
    try:
        conn = get_conn()
        print("✅ DB 연결 성공\n")
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print("   .env 파일의 MYSQL_HOST / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB 를 확인하세요.")
        return

    create_tables(conn)
    create_boards(conn)
    create_admin(conn)
    conn.close()
    print("\n🎉 초기화 완료! `python app.py` 로 서버를 시작하세요.")


if __name__ == '__main__':
    print("=" * 50)
    print("  ANAM DB 초기화")
    print("=" * 50 + "\n")
    init()
