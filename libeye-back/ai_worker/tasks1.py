import os
import uuid
import boto3
from botocore.client import Config
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models # API 서버와 공유하는 DB 모델 (models.py)

# 1. Celery 및 Redis 설정 (API 서버와 동일한 브로커 공유)
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("libeye_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# 2. DB 연결 설정
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:libeye_admin_pwd@postgres:5432/libeye_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. MinIO 설정
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
s3_client = boto3.client(
    's3', endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "admin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "admin1234"),
    config=Config(signature_version='s3v4')
)

def download_image_from_minio(object_name: str) -> str:
    """MinIO에서 이미지를 다운로드하여 로컬 임시 파일 경로를 반환합니다."""
    local_path = f"/tmp/{uuid.uuid4()}.jpg"
    s3_client.download_file("original-bucket", object_name, local_path)
    return local_path

def run_vlm_inference(image_path: str):
    """
    [TODO] 실제 Gemma4 VLM 모델 또는 객체 탐지 모델 추론 로직
    보고서 설계안 5장: LIS 알고리즘 및 Bounding Box 추출 로직 구현 부분
    """
    # 임시 목(Mock) 데이터 반환
    return [
        {"bbox": {"x": 10, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12가", "confidence": 0.95},
        {"bbox": {"x": 45, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12나", "confidence": 0.92},
        # ... 추가 인식 결과
    ]

def evaluate_lis_algorithm(detections: list, db_session) -> list:
    """
    [TODO] LIS(Longest Increasing Subsequence) 알고리즘 적용 및 DB 데이터 비교
    추출된 텍스트와 DB의 expected_order를 비교하여 상태(MATCH, MISPLACED 등) 판별
    """
    results = []
    for i, det in enumerate(detections):
        # 임시 상태 부여 (추후 실제 로직으로 교체)
        status = "MATCH" if i == 0 else "MISPLACED"
        results.append({
            "bounding_box": det["bbox"],
            "ocr_text": det["text"],
            "confidence": det["confidence"],
            "detected_order": i + 1,
            "status": status,
            "matched_book_id": "BOOK-MOCK-ID" # 실제로는 DB 조회 결과
        })
    return results

@celery_app.task(bind=True, name="process_scan_image")
def process_scan_image(self, session_id: str, location_id: str, image_object_name: str):
    """
    API 서버가 큐에 넣은 비동기 작업을 실제로 수행하는 메인 함수
    """
    db = SessionLocal()
    image_path = None
    try:
        # 1. 이미지 다운로드 (MinIO -> 로컬)
        image_path = download_image_from_minio(image_object_name)

        # 2. VLM 모델 추론 (Gemma4 등)
        detections = run_vlm_inference(image_path)

        # 3. 데이터베이스 매칭 및 LIS 알고리즘 검증
        analyzed_results = evaluate_lis_algorithm(detections, db)

        # 4. 분석 결과를 DB에 저장 (Scan_Result_Detail)
        for res in analyzed_results:
            new_detail = models.ScanResultDetail(
                session_id=uuid.UUID(session_id),
                matched_book_id=res["matched_book_id"],
                ocr_text=res["ocr_text"],
                confidence=res["confidence"],
                bounding_box=res["bounding_box"],
                detected_order=res["detected_order"],
                status=res["status"]
            )
            db.add(new_detail)

        # 5. 세션 상태 업데이트 (PROCESSING -> COMPLETED/NEEDS_ACTION)
        session = db.query(models.ScanSession).filter(models.ScanSession.session_id == session_id).first()
        if session:
            # 하나라도 MISPLACED가 있으면 NEEDS_ACTION 처리
            has_error = any(r["status"] != "MATCH" for r in analyzed_results)
            session.overall_status = "NEEDS_ACTION" if has_error else "COMPLETED"

        db.commit()
        return {"status": "success", "session_id": session_id}

    except Exception as e:
        db.rollback()
        # 실패 시 세션 상태를 ERROR로 변경
        session = db.query(models.ScanSession).filter(models.ScanSession.session_id == session_id).first()
        if session:
            session.overall_status = "ERROR"
            db.commit()
        # Celery 재시도 로직 호출 (옵션)
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()
        # 임시 다운로드 파일 삭제
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
