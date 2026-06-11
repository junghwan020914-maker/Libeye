# 리팩토링 노트 — 발견된 문제점 정리

2026-06-11 구조 리팩토링(플랫 구조 → `app/` 패키지 구조) 중 코드를 전수 검토하면서 발견한 문제점입니다.
**이번 리팩토링에서는 동작 불변 원칙에 따라 수정하지 않고 그대로 옮겼으며**, 아래 항목들은 추후 별도 작업으로 고치는 것을 권장합니다.

## 1. seed.py의 자체 DB 연결 + URL 불일치 (`app/core/seed.py`)

- `seed.py`가 `app/database.py`의 engine을 쓰지 않고 **자체 engine/SessionLocal을 별도로 생성**합니다.
- 게다가 환경변수 없을 때의 기본 URL이 서로 다릅니다:
  - `database.py`: `postgresql://postgres:libeye_admin_pwd@postgres:5432/libeye_db`
  - `seed.py`: `postgresql://postgres:capstone123@postgres:5432/capstone_db`
- Docker에서는 `DATABASE_URL` 환경변수가 항상 주입되어 문제가 안 드러나지만, 로컬에서 env 없이 실행하면 **시딩과 API가 서로 다른 DB를 바라봅니다**.
- **권장**: seed.py의 자체 engine을 삭제하고 `from app.database import engine, SessionLocal` 사용.

## 2. MinIO 자격증명 하드코딩 (`app/core/storage.py`)

- 구 main.py에서 옮겨온 `s3_client`는 `admin` / `admin1234`가 **코드에 하드코딩**되어 있습니다.
- 같은 파일 상단의 `get_s3_client()`는 환경변수(`MINIO_ACCESS_KEY` 등)를 쓰고 있어 **한 파일 안에 두 방식이 공존**합니다.
- **권장**: `app/config.py`를 만들어 환경변수 기반 설정으로 통일 (`os.getenv("MINIO_ACCESS_KEY", "admin")` 형태면 기존 동작 유지됨).

## 3. storage.py의 presigned URL 헬퍼는 데드 코드

- `get_presigned_upload_url()` / `get_presigned_download_url()`은 **api 코드 어디에서도 import하지 않습니다** (이미지 전달은 전부 image_proxy 라우터 경유).
- `EXTERNAL_MINIO_ENDPOINT = "localhost:9000"`도 하드코딩이라 배포 환경에서 동작하지 않습니다.
- **권장**: 사용 계획이 없으면 삭제, 쓸 거라면 endpoint를 환경변수화.

## 4. LIS 오배열 재계산 로직 중복 (`app/routers/results.py`)

- `force_match_detection()`(강제 매칭)과 `delete_false_detection()`(오탐 삭제)에 **동일한 ~40줄짜리 LIS(최장 증가 부분 수열) 재계산 블록이 복붙**되어 있습니다.
- 한쪽만 수정하면 두 엔드포인트의 판정 결과가 달라지는 버그로 직결됩니다.
- **권장**: `recalculate_misplacement(db, session_id)` 함수 하나로 추출 (향후 `app/services/results_service.py`).
- 부가: 루프 안에서 책마다 `db.query(BookMaster).filter_by(...)`를 호출하는 N+1 쿼리 패턴도 있음 — 책이 많아지면 느려짐.

## 5. Pydantic 응답 스키마 부재

- 모든 라우터가 raw dict를 반환합니다 (`response_model` 미사용). 요청 스키마는 `results.py`의 `MatchRequest` 하나뿐.
- API 문서(`/docs`)에 응답 형식이 안 나오고, 오타로 키가 빠져도 검증이 안 됩니다.
- **권장**: `app/schemas/` 디렉토리를 만들어 주요 엔드포인트부터 도입.
  주의: `response_model`을 붙이면 스키마에 없는 키는 응답에서 **조용히 제거**되므로, 기존 dict의 모든 키를 빠짐없이 스키마에 넣어야 프론트엔드가 깨지지 않습니다.

## 6. 라우터에 비즈니스 로직 직접 포함

- `results.py`(267줄)에 LIS 알고리즘, URL 변환, 집계 로직이 전부 들어 있고, `sessions.py`/`cart.py`도 MinIO 업로드 + DB 저장 + Celery 발행을 엔드포인트 함수 안에서 직접 수행합니다.
- **권장**: `app/services/` 계층을 만들어 라우터는 요청/응답 처리만 담당하도록 분리.

## 7. CORS 설정 모순 (`app/main.py`)

- `allow_origins=["*"]` + `allow_credentials=True` 조합은 CORS 스펙상 함께 쓸 수 없습니다 (브라우저가 credentials 요청 시 와일드카드 origin을 거부; Starlette가 요청 origin을 echo해주는 방식으로 우회 동작 중).
- **권장**: 배포 시 실제 프론트엔드 origin을 명시.

## 8. 기타 소소한 것들

- `app/routers/results.py`, `image_proxy.py`: `Request` import가 미사용.
- `app/routers/history.py`, `search.py`: `Query` import가 미사용 (search는 사용 중, history는 미사용).
- `app/models/cart.py`: `datetime.utcnow`는 Python 3.12+에서 deprecated — `datetime.now(timezone.utc)` 권장.
- `app/core/celery_client.py`의 task 스텁 2개(`process_scan_session`, `process_cart_task`)는 본문이 `pass`이고 실제로는 `send_task()`(이름 기반)만 사용하므로 없어도 동작합니다. 문서 역할로만 존재.
- `worker.py`(현 celery_client.py)와 ai_worker의 Celery 설정(timezone 등)이 별도 관리되므로 변경 시 양쪽 동기화 필요.
- `api/models.py`와 `ai_worker/models.py`가 **동일한 스키마의 복사본**입니다 — 한쪽만 수정하면 워커/API 간 스키마가 어긋납니다. (이번 리팩토링으로 api 쪽은 `app/models/`로 분할되어 구조가 달라졌으니 더 주의 필요.)

## 이번 리팩토링에서 실제로 바뀐 것 (동작 영향 없음)

- 파일 구조: 플랫 → `app/` 패키지 (`models/`, `routers/`, `core/` 분리), import 전부 `from app.xxx import ...` 절대경로로 변경.
- `POST /api/v1/sessions` 엔드포인트가 main.py에서 `app/routers/sessions.py`로 이동 (경로·동작 동일).
- main.py가 자체 생성하던 중복 Celery 클라이언트 제거 → `app/core/celery_client.py`의 `celery_app` 단일 사용 (broker/backend URL 동일).
- main.py·cart.py가 각각 만들던 boto3 클라이언트 → `app/core/storage.py`의 `s3_client` 공용 사용 (설정값 동일).
- `seed.py`의 seed-data.sql 경로 계산 수정 (파일이 두 단계 깊어졌기 때문 — 유일한 필수 코드 수정).
- Dockerfile CMD: `main:app` → `app.main:app`.
- Celery 태스크 이름(`process_session_task`, `process_cart_task`)과 모든 API 경로·응답 형식은 변경 없음.
