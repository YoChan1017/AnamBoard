import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-please-change')

    MYSQL_HOST     = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT     = int(os.getenv('MYSQL_PORT', 3307))
    MYSQL_USER     = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB       = os.getenv('MYSQL_DB', 'anam')
    MYSQL_SSL      = os.getenv('MYSQL_SSL', 'false').lower() == 'true'
    MYSQL_SSL_CA   = os.getenv('MYSQL_SSL_CA', None)   # Aiven CA 인증서 경로

    BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_MB', 16)) * 1024 * 1024

    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',
                          'zip', 'doc', 'docx', 'xls', 'xlsx', 'hwp'}

    POSTS_PER_PAGE = 10

    # 역할 상수
    ROLE_USER  = 1
    ROLE_ADMIN = 9
