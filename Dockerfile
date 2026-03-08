# 1. Python 3.9 이미지 사용
FROM python:3.9-slim

# 2. 필수 패키지 설치 및 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치
# requirements.txt가 없다면 아래 라이브러리들을 설치하도록 구성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 전체 복사
COPY . .

# 5. Flask 실행 포트 노출
EXPOSE 5000

# 6. 애플리케이션 실행
CMD ["python", "app.py"]