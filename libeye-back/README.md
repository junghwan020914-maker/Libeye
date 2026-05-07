📚 LibEye 백엔드 시스템 (On-Premises 최적화)

본 프로젝트는 도서관 내부망에서 작동하도록 설계된 스마트 서고 관리 시스템의 백엔드입니다. 외부 클라우드(AWS S3, RDS)를 사용하지 않고 Docker 기반의 로컬 인프라(FastAPI, PostgreSQL, MinIO, Redis, Celery)를 구축합니다.

1. 프로젝트 폴더 구조

지금까지 생성한 파일들을 아래 구조에 맞게 배치해 주세요.

libeye-backend/
├── docker-compose.yml         # 1. 전체 컨테이너 실행 설정
├── init-db/
│   └── 01-init.sql            # 2. PostgreSQL 초기화 스크립트
├── nginx/
│   └── nginx.conf             # (추후 작성) Nginx 프록시 설정
├── api/                       # API 서버 폴더
│   ├── main.py                # 3. FastAPI 메인 로직 (V2)
│   ├── models.py              # 4. DB ORM 모델
│   ├── database.py            # 5. DB 연결 설정
│   ├── storage.py             # 6. MinIO S3 연동 모듈
│   ├── worker.py              # 7. Celery 워커 설정
│   ├── requirements.txt       # [신규] API 패키지 목록
│   └── Dockerfile             # [신규] API 서버 도커 설정
└── ai_worker/                 # AI 워커 폴더
    ├── tasks.py               # 8. 비동기 AI 분석 로직
    ├── models.py              # (api/models.py 복사 혹은 심볼릭 링크)
    ├── requirements.txt       # [신규] 워커 패키지 목록
    └── Dockerfile             # [신규] 워커 도커 설정


2. Docker 빌드 파일 준비 (신규)

컨테이너를 실행하기 위해 각 폴더에 아래의 설정 파일을 추가로 생성해야 합니다.

api/requirements.txt

fastapi==0.104.1
uvicorn==0.24.0.post1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
boto3==1.29.3
celery==5.3.4
redis==5.0.1
pydantic==2.5.2


api/Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# FastAPI 서버 실행 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


ai_worker/requirements.txt

celery==5.3.4
redis==5.0.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
boto3==1.29.3
# torch, transformers 등 AI 모델 관련 패키지는 추후 추가


ai_worker/Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Celery 워커 실행 명령어
CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info", "--pool=solo"]


3. 시스템 실행 방법

모든 파일 배치가 끝났다면, 터미널에서 libeye-backend 최상위 폴더로 이동한 후 아래 명령어를 실행합니다.

# 전체 백엔드 시스템 빌드 및 백그라운드 실행
docker-compose up -d --build

# 실행 상태 확인
docker-compose ps

# 로그 확인 (문제가 발생할 경우)
docker-compose logs -f


4. 로컬 접속 및 API 테스트 흐름

시스템이 구동되면 아래 주소를 통해 접속할 수 있습니다.

API 문서 (Swagger UI): http://localhost:8000/docs

MinIO 콘솔 (S3 스토리지): http://localhost:9001 (ID: admin, PW: admin1234)

✅ 전체 프로세스 테스트 시나리오 (Swagger UI 활용)

세션 생성 (POST /api/v1/sessions)

Request Body에 location_id (예: "LOC-A-1")와 user_id를 넣고 요청합니다.

반환된 session_id (UUID)를 복사해둡니다.

업로드 URL 발급 (GET /api/v1/sessions/{session_id}/upload-url)

방금 얻은 session_id를 넣고 호출하면, MinIO로 직접 업로드할 수 있는 긴 주소(upload_url)가 반환됩니다.

이미지 업로드 (Postman 또는 클라이언트)

발급받은 URL로 로컬의 테스트 이미지를 PUT 메서드로 업로드합니다.

분석 시작 (POST /api/v1/sessions/{session_id}/analyze)

업로드가 완료되면 해당 API를 호출하여 AI 워커(Celery)로 작업을 던집니다.

결과 확인 (GET /api/v1/sessions/{session_id}/results)

AI 워커가 작업을 마쳤을 즈음 호출하면, 임시 다운로드 이미지 URL과 VLM 객체 탐지 결과(Bounding Box, OCR Text 등)가 출력됩니다.
