# 1. 베이스 이미지 설정 (Python 3.10 Slim 버전)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. [핵심 수정] 이미지 처리 및 DB 연결에 필요한 시스템 라이브러리 설치
# 최신 데비안에서는 libgl1-mesa-glx 대신 libgl1을 사용합니다.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. 패키지 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 및 모델 가중치 복사
COPY . .

# 6. Celery 워커 실행 명령 (프로젝트명 libeye 반영)
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
