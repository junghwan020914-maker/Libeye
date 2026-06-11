# 1. 파이썬 3.10 슬림 버전 사용
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. [핵심 에러 해결] C 확장 모듈(psycopg2 등) 컴파일에 필요한 필수 시스템 라이브러리 설치
# ai-worker와 동일하게 이 부분이 누락되면 pip install psycopg2-binary 과정에서 에러가 납니다.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. 패키지 목록 복사 및 설치 (도커 레이어 캐싱)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. FastAPI 서버 (Uvicorn) 실행 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
