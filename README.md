# ANAM 커뮤니티 - 다중 게시판 Flask 앱

## 📁 프로젝트 구조

```
flask_community/
├── app.py                  # 앱 팩토리 & 메인 엔트리포인트
├── config.py               # 환경변수 기반 설정
├── db.py                   # DB 연결 헬퍼
├── init_db.py              # 초기 데이터 삽입 스크립트
├── requirements.txt
├── .env.example            # 환경변수 템플릿
├── routes/
│   ├── auth.py             # 로그인 / 로그아웃 / 회원가입
│   ├── board.py            # 게시판 목록/글CRUD/댓글/첨부파일
│   ├── admin.py            # 관리자 - 사용자·게시판 관리
│   └── user.py             # 내 정보 수정 / 내가 쓴 글
├── templates/
│   ├── base.html           # 공통 레이아웃 (사이드바 포함)
│   ├── auth/               # login.html, register.html
│   ├── board/              # list, view, write
│   ├── admin/              # dashboard, users, boards, forms
│   └── user/               # profile, my_posts
└── static/
    ├── css/style.css
    └── uploads/            # 첨부파일 저장 경로
```

## ⚙️ 설치 & 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 DB 연결 정보 입력
```

#### 로컬 MySQL 예시 (`.env`)
```
SECRET_KEY=my-secret-key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=anam
MYSQL_SSL=false
```

#### Aiven MySQL 예시 (`.env`)
```
SECRET_KEY=my-secret-key
MYSQL_HOST=mysql-xxxx.aivencloud.com
MYSQL_PORT=23291
MYSQL_USER=avnadmin
MYSQL_PASSWORD=AVNS_xxxxxxxxxxxx
MYSQL_DB=anam
MYSQL_SSL=true
MYSQL_SSL_CA=ca.pem          # Aiven 콘솔 > Service > Download CA Certificate
```

> Aiven CA 인증서(`ca.pem`)는 Aiven 콘솔에서 다운로드 후 프로젝트 루트에 저장

### 3. DB 생성 & 초기화
```bash
# MySQL에서 먼저 DB 생성 (SQL_생성문.txt 실행)
mysql -u root -p < SQL_생성문.sql

# 기본 게시판 3개 + 관리자 계정 생성
python init_db.py
```

초기 관리자 계정:
- **아이디**: `admin`
- **비밀번호**: `admin1234`

> `init_db.py` 실행 전에 `.env`의 `ADMIN_PASSWORD`를 변경하거나, 로그인 후 반드시 비밀번호를 수정하세요.

### 4. 앱 실행
```bash
python app.py
# 또는
flask run
```
→ http://127.0.0.1:5000

## 🗂️ 주요 기능

| 기능 | URL |
|------|-----|
| 게시판 목록 | `/board/<code>` |
| 글 보기 | `/board/<code>/<post_id>` |
| 글쓰기 | `/board/<code>/write` |
| 관리자 대시보드 | `/admin/` |
| 사용자 관리 | `/admin/users` |
| 게시판 관리 | `/admin/boards` |
| 내 정보 수정 | `/user/profile` |
| 내가 쓴 글 | `/user/my-posts` |

## 🔐 역할 (role)
| 값 | 설명 |
|----|------|
| 1 | 일반 사용자 |
| 9 | 관리자 |

## 📌 기본 게시판
| 코드 | 이름 | 읽기 | 쓰기 |
|------|------|------|------|
| `notice` | 공지사항 | 1 (전체) | 9 (관리자) |
| `free` | 자유게시판 | 1 (전체) | 1 (전체) |
| `qna` | 질문&건의사항 | 1 (전체) | 1 (전체) |
