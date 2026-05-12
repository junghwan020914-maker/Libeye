import os
import uuid
import boto3
from botocore.client import Config
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import difflib  # Levenshtein distance 대안 (문자열 유사도 측정용 내장 라이브러리)

import models # api 폴더에서 복사해온 models.py

# --- [인프라 설정] ---
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("libeye_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:libeye_admin_pwd@postgres:5432/libeye_db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
s3_client = boto3.client(
    's3', endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "admin"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "admin1234"),
    config=Config(signature_version='s3v4')
)

# --- [1. Vision AI 파이프라인 (추후 Gemma4 연동부)] ---
class VisionLanguagePipeline:
    def __init__(self):
        # TODO: 실제 서버 환경에서 HuggingFace Transformers 모듈 로드
        # self.model = AutoModelForCausalLM.from_pretrained("google/gemma-4-vision")
        # self.processor = AutoProcessor.from_pretrained(...)
        print("Vision Model Initialized.")

    def analyze_image(self, image_path: str):
        """
        이미지에서 책등 Bounding Box와 OCR 텍스트를 추출합니다.
        (현재는 로직 테스트를 위한 가상 데이터 반환)
        """
        # 실제 로직: image = Image.open(image_path) -> bbox 및 ocr 추론
        return [
            {"bbox": {"x": 10, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12가", "confidence": 0.95},
            {"bbox": {"x": 45, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12다", "confidence": 0.92}, # 의도적인 오배열 (나->다)
            {"bbox": {"x": 80, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12나", "confidence": 0.88}, # 의도적인 오배열
            {"bbox": {"x": 115, "y": 20, "w": 30, "h": 100}, "text": "813.6 김12라", "confidence": 0.97},
        ]

vlm_pipeline = VisionLanguagePipeline() # 워커 메모리에 모델 미리 로드

# --- [2. 핵심 알고리즘 구현부] ---

def match_books_with_db(detections: list, location_id: str, db_session) -> list:
    """
    1단계: OCR 텍스트와 DB의 도서 정보를 매칭하여 '원래 있어야 할 순서(expected_order)'를 찾습니다.
    설계안에 따라 문자열 유사도 90% 이상인 경우 매칭 성공으로 간주합니다.
    """
    # 해당 서가의 모든 도서 마스터 정보 조회
    expected_books = db_session.query(models.BookMaster).filter(
        models.BookMaster.assigned_loc_id == location_id
    ).all()
    
    matched_results = []
    
    for idx, det in enumerate(detections):
        ocr_text = det["text"]
        best_match = None
        highest_ratio = 0.0
        
        # Levenshtein 기반 유사도(difflib) 측정
        for book in expected_books:
            ratio = difflib.SequenceMatcher(None, ocr_text, book.call_number).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = book
        
        # 유사도가 0.9(90%) 이상이면 매칭 성공
        if best_match and highest_ratio >= 0.9:
            matched_results.append({
                "bbox": det["bbox"],
                "ocr_text": ocr_text,
                "confidence": det["confidence"],
                "detected_order": idx + 1, # 사진상 왼쪽부터의 순서
                "matched_book_id": best_match.book_id,
                "expected_order": best_match.expected_order, # LIS 판별의 핵심
                "status": "PENDING"
            })
        else:
            # 매칭 실패 시 UNKNOWN 처리 (외부 도서이거나 인식 불량)
            matched_results.append({
                "bbox": det["bbox"],
                "ocr_text": ocr_text,
                "confidence": det["confidence"],
                "detected_order": idx + 1,
                "matched_book_id": None,
                "expected_order": -1,
                "status": "UNKNOWN"
            })
            
    return matched_results

def evaluate_lis_algorithm(matched_data: list) -> list:
    """
    2단계: LIS (Longest Increasing Subsequence) 알고리즘을 적용하여
    오배열(MISPLACED)된 도서를 색출합니다.
    """
    # 매칭 성공한 책들만 필터링하여 순서 배열 생성
    valid_books = [b for b in matched_data if b["status"] == "PENDING"]
    n = len(valid_books)
    
    if n == 0:
        return matched_data

    # DP를 이용한 LIS 계산 및 경로 추적
    dp = [1] * n
    prev = [-1] * n
    
    for i in range(1, n):
        for j in range(i):
            if valid_books[i]["expected_order"] > valid_books[j]["expected_order"]:
                if dp[i] < dp[j] + 1:
                    dp[i] = dp[j] + 1
                    prev[i] = j
                    
    # 최대 길이의 LIS 마지막 인덱스 찾기
    max_len = 0
    max_idx = -1
    for i in range(n):
        if dp[i] > max_len:
            max_len = dp[i]
            max_idx = i
            
    # LIS에 속하는(순서가 올바른) 인덱스 역추적
    lis_indices = set()
    curr = max_idx
    while curr != -1:
        lis_indices.add(curr)
        curr = prev[curr]
        
    # 상태 업데이트 (LIS에 속하면 MATCH, 아니면 MISPLACED)
    for i, book in enumerate(valid_books):
        if i in lis_indices:
            book["status"] = "MATCH"
        else:
            book["status"] = "MISPLACED"
            
    return matched_data

# --- [3. 메인 Celery 비동기 Task] ---

@celery_app.task(bind=True, name="process_scan_image")
def process_scan_image(self, session_id: str, location_id: str, image_object_name: str):
    db = SessionLocal()
    image_path = f"/tmp/{uuid.uuid4()}.jpg"
    
    try:
        # 1. MinIO에서 스캔 이미지 다운로드
        s3_client.download_file("original-bucket", image_object_name, image_path)

        # 2. VLM 모델을 통한 텍스트 및 Bounding Box 추출
        raw_detections = vlm_pipeline.analyze_image(image_path)

        # 3. DB 데이터와 OCR 결과 매칭 (유사도 검사)
        matched_books = match_books_with_db(raw_detections, location_id, db)

        # 4. LIS 알고리즘으로 오배열 판별
        final_results = evaluate_lis_algorithm(matched_books)

        # 5. 결과를 데이터베이스에 저장
        has_error = False
        for res in final_results:
            new_detail = models.ScanResultDetail(
                session_id=uuid.UUID(session_id),
                matched_book_id=res["matched_book_id"],
                ocr_text=res["ocr_text"],
                confidence=res["confidence"],
                bounding_box=res["bbox"],
                detected_order=res["detected_order"],
                status=res["status"]
            )
            db.add(new_detail)
            if res["status"] in ["MISPLACED", "UNKNOWN"]:
                has_error = True

        # 6. 세션 최종 상태 업데이트
        session = db.query(models.ScanSession).filter(models.ScanSession.session_id == session_id).first()
        if session:
            session.overall_status = "NEEDS_ACTION" if has_error else "COMPLETED"

        db.commit()
        return {"status": "success", "session_id": session_id}

    except Exception as e:
        db.rollback()
        session = db.query(models.ScanSession).filter(models.ScanSession.session_id == session_id).first()
        if session:
            session.overall_status = "ERROR"
            db.commit()
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()
        if os.path.exists(image_path):
            os.remove(image_path)
