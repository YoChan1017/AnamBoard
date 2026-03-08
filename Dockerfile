# Python 3.11 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리
WORKDIR /app

# 시스템 패키지 (cryptography 빌드에 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
# requirements.txt가 없다면 아래 라이브러리들을 설치하도록 구성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 전체 복사
COPY . .

# Flask 실행 포트 노출
EXPOSE 5000

# 컨테이너 시작 시 테이블 초기화 후 앱 실행
CMD ["sh", "-c", "python init_db.py && python app.py"]