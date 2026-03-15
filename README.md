# ANAM 커뮤니티 - 다중 게시판 Flask 앱

Flask + MySQL(PyMySQL) 기반의 다중 게시판 커뮤니티 웹 애플리케이션입니다.  
관리자 페이지, 사용자 정보 관리, 파일 첨부, Docker 배포, GitHub Actions CI/CD를 모두 포함합니다.

---

## 📁 프로젝트 구조

```
flask_community/
├── app.py                  # 앱 팩토리 & 메인 엔트리포인트
├── config.py               # 환경변수 기반 설정
├── db.py                   # DB 연결 헬퍼 (PyMySQL, g 캐싱)
├── init_db.py              # 테이블 생성 + 초기 데이터 삽입 스크립트
├── requirements.txt        # 의존성 패키지
├── Dockerfile              # Docker 이미지 빌드 설정
├── docker-compose.yml      # 로컬 개발용 (MySQL + Flask 컨테이너)
├── .env.example            # 환경변수 템플릿
├── .gitignore
├── SQL_생성문.txt           # 수동 DB 생성용 DDL
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions CI/CD (빌드 → Docker Hub → SSH 배포)
├── routes/
│   ├── __init__.py
│   ├── auth.py             # 로그인 / 로그아웃 / 회원가입
│   ├── board.py            # 게시판 목록 / 글 CRUD / 댓글 / 첨부파일 다운로드
│   ├── admin.py            # 관리자 - 사용자·게시판 관리
│   └── user.py             # 내 정보 수정 / 내가 쓴 글
├── templates/
│   ├── base.html           # 공통 레이아웃 (사이드바 + 네비게이션)
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── board/
│   │   ├── list.html       # 게시판 목록 (공지 상단 고정, 검색, 페이지네이션)
│   │   ├── view.html       # 글 상세 (댓글, 비밀글, 첨부파일 다운로드)
│   │   └── write.html      # 글 작성 / 수정 (파일 첨부)
│   ├── admin/
│   │   ├── base_admin.html # 관리자 전용 레이아웃
│   │   ├── dashboard.html  # 통계 카드 + 최근 가입/게시글
│   │   ├── users.html      # 사용자 목록 (검색, 활성/비활성 토글)
│   │   ├── user_edit.html  # 사용자 수정 (닉네임, 이메일, 역할, 활성화)
│   │   ├── boards.html     # 게시판 목록 (수정, 비활성화)
│   │   └── board_form.html # 게시판 생성 / 수정 폼
│   └── user/
│       ├── profile.html    # 내 정보 수정 + 비밀번호 변경
│       └── my_posts.html   # 내가 쓴 글 목록 (수정/삭제)
└── static/
    ├── css/style.css
    └── uploads/            # 첨부파일 저장 경로 (볼륨 마운트)
```

---

## ✨ 주요 기능

| 분류 | 기능 |
|------|------|
| **인증** | 회원가입, 로그인/로그아웃, 세션 관리 |
| **게시판** | 다중 게시판, 공지 상단 고정, 비밀글, 검색, 페이지네이션 |
| **게시글** | 작성·수정·삭제, 조회수, 공지·비밀 옵션 |
| **첨부파일** | 다중 파일 업로드(최대 16MB), 다운로드, 수정 시 개별 삭제 |
| **댓글** | 비밀 댓글, 소프트 삭제 |
| **관리자** | 대시보드 통계, 사용자 관리(수정·활성화 토글), 게시판 CRUD |
| **마이페이지** | 내 정보 수정, 비밀번호 변경, 내가 쓴 글 관리 |
| **배포** | Docker, Docker Hub, GitHub Actions CI/CD, Aiven MySQL(SSL) 지원 |

---

## 🗂️ URL 구조

| 기능 | URL |
|------|-----|
| 홈 (첫 번째 게시판으로 리다이렉트) | `/` |
| 게시판 목록 | `/board/<code>` |
| 글 보기 | `/board/<code>/<post_id>` |
| 글쓰기 | `/board/<code>/write` |
| 파일 다운로드 | `/download/<file_id>` |
| 로그인 | `/login` |
| 회원가입 | `/register` |
| 내 정보 수정 | `/user/profile` |
| 내가 쓴 글 | `/user/my-posts` |
| 관리자 대시보드 | `/admin/` |
| 사용자 관리 | `/admin/users` |
| 게시판 관리 | `/admin/boards` |

---

## 🔐 역할 (role)

| 값 | 설명 |
|----|------|
| `1` | 일반 사용자 |
| `9` | 관리자 (사용자·게시판 관리, 공지글 작성 가능) |

---

## 📌 기본 게시판

`init_db.py` 실행 시 자동 생성됩니다.

| 코드 | 이름 | 타입 | 읽기 권한 | 쓰기 권한 |
|------|------|------|-----------|-----------|
| `notice` | 공지사항 | NOTICE | 1 (전체) | 9 (관리자) |
| `free` | 자유게시판 | NORMAL | 1 (전체) | 1 (전체) |
| `qna` | 질문&건의사항 | NORMAL | 1 (전체) | 1 (전체) |

---

## ⚙️ 로컬 설치 & 실행

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

```env
SECRET_KEY=my-secret-key-change-this

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=anam
MYSQL_SSL=false

# 관리자 초기 계정 (init_db.py 실행 시 사용)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin1234
ADMIN_NICKNAME=관리자

# 업로드 최대 크기 (MB)
MAX_UPLOAD_MB=16
```

#### Aiven MySQL 예시 (`.env`)

```env
SECRET_KEY=my-secret-key-change-this

MYSQL_HOST=mysql-xxxx.aivencloud.com
MYSQL_PORT=23291
MYSQL_USER=avnadmin
MYSQL_PASSWORD=AVNS_xxxxxxxxxxxx
MYSQL_DB=anam
MYSQL_SSL=true
MYSQL_SSL_CA=ca.pem          # Aiven 콘솔 > Service > Download CA Certificate

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin1234
ADMIN_NICKNAME=관리자

MAX_UPLOAD_MB=16
```

> Aiven CA 인증서(`ca.pem`)는 Aiven 콘솔에서 다운로드 후 프로젝트 루트에 저장하세요.

### 3. DB 생성 & 초기화

```bash
# MySQL에서 먼저 DB 생성
mysql -u root -p -e "CREATE DATABASE anam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 테이블 생성 + 기본 게시판 3개 + 관리자 계정 생성
python init_db.py
```

초기 관리자 계정:
- **아이디**: `admin`  
- **비밀번호**: `admin1234`

> ⚠️ 로그인 후 반드시 **내 정보 > 비밀번호 변경**에서 비밀번호를 수정하세요.

### 4. 앱 실행

```bash
python app.py
# 또는
flask run
```

→ http://127.0.0.1:5000

---

## 🐳 Docker로 실행 (로컬 개발)

MySQL + Flask를 한 번에 실행합니다.

```bash
# .env 파일 준비 후 실행
docker compose up -d

# 최초 실행 시 init_db.py는 CMD에서 자동 실행됨
# 로그 확인
docker compose logs -f web
```

`docker-compose.yml`의 기본 설정:
- MySQL 8.0 (포트 `3306`)  
- Flask 앱 (포트 `5000`)  
- 첨부파일은 `uploads` 볼륨에 영구 보존

---

## 🚀 GitHub Actions CI/CD 배포

`main` 브랜치에 push하면 자동으로 **Docker 이미지 빌드 → Docker Hub 푸시 → SSH 서버 배포** 가 실행됩니다.

### 필요한 GitHub Secrets 등록

저장소 **Settings > Secrets and variables > Actions** 에서 아래 항목을 등록합니다.

| Secret 이름 | 설명 |
|-------------|------|
| `DOCKERHUB_USERNAME` | Docker Hub 아이디 |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token |
| `SSH_HOST` | 배포 서버 IP 또는 도메인 |
| `SSH_USER` | SSH 접속 유저명 (예: `ubuntu`) |
| `SSH_PRIVATE_KEY` | SSH 개인키 전체 내용 (`-----BEGIN ...`) |
| `SSH_PORT` | SSH 포트 (기본값 `22`) |
| `ENV_FILE` | `.env` 파일 내용 전체 |
| `CA_PEM` | Aiven `ca.pem` 파일 내용 전체 (Aiven 미사용 시 빈 값) |

### 배포 흐름

```
git push origin main
    │
    ▼
[Job 1: build]
  - Docker 이미지 빌드
  - Docker Hub에 :latest 및 :<sha> 태그로 푸시
    │
    ▼
[Job 2: deploy]
  - SSH로 서버 접속
  - .env, ca.pem, docker-compose.yml 생성
  - docker compose pull → down → up -d
  - 오래된 이미지 정리
```

### 배포 서버 사전 준비

```bash
# 배포 서버에 Docker & Docker Compose 설치
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

---

## 🗄️ DB 스키마 요약

```
users         회원 정보 (username BINARY, role, is_active)
boards        게시판 (code, type, read_role, write_role, is_active)
posts         게시글 (is_notice, is_secret, status: active|deleted)
comments      댓글 (is_secret, is_deleted 소프트 삭제)
attachments   첨부파일 (post 삭제 시 CASCADE)
```

전체 DDL은 `SQL_생성문.txt` 또는 `init_db.py` 참조.

---

## 📦 의존성

```
Flask==3.0.3
PyMySQL==1.1.1
cryptography==42.0.8   # Aiven SSL 연결에 필요
python-dotenv==1.0.1
Werkzeug==3.0.3
```

---

## 🛠️ 개발 팁

- `FLASK_DEBUG=true` 환경변수 설정 시 디버그 모드로 실행됩니다.
- 첨부파일 허용 확장자는 `config.py`의 `ALLOWED_EXTENSIONS`에서 수정합니다.
- 게시판 권한은 `read_role` / `write_role` 값으로 제어합니다 (`1`=일반, `9`=관리자).
- 관리자는 자기 자신의 계정을 비활성화하거나 관리자 권한을 강등할 수 없습니다.

---

&copy; 2025 ANAM Community
