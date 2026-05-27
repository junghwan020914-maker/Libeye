from celery import shared_task
import tempfile
import os
import cv2
import base64
import boto3  # requests 대신 boto3 사용

# 실제 구현된 함수명으로 올바르게 임포트
from service.detector import run_detection, crop_spine
from service.ocr import extract_text_with_gemma
from service.matcher import get_top_candidates, hybrid_book_matching_with_jamo
from service.cart_sorter import CartSorter

from database import SessionLocal
from models_cart import CartSession, CartItem

# MinIO 클라이언트 설정 (인증 정보 포함)
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id="admin",
    aws_secret_access_key="admin1234"
)

@shared_task(name="process_cart_task")
def process_cart_job(session_id: int, image_url: str):
    db = SessionLocal()
    temp_file_path = None
    
    try:
        # 1. 세션 상태 업데이트
        session = db.query(CartSession).filter(CartSession.id == session_id).first()
        if not session:
            return
        session.status = "PROCESSING"
        db.commit()

        # 2. MinIO에서 이미지 다운로드 (boto3 인증 사용)
        file_name = image_url.split("/")[-1] # URL에서 파일명만 추출 (예: cart-cb4e4420.jpg)
        
        fd, temp_file_path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            # original-bucket에서 해당 파일을 다운로드하여 임시 파일에 쓰기
            s3_client.download_fileobj('original-bucket', file_name, f)

        # 3. OpenCV로 이미지 읽기
        img = cv2.imread(temp_file_path)
        if img is None:
            raise Exception("이미지 파일을 읽을 수 없습니다.")

        # 4. YOLO 모델을 통한 책등 탐지 (detector.py)
        boxes, masks = run_detection(img)
        
        raw_books = []
        
        if boxes is not None:
            # 추출된 각 책등에 대하여 반복
            for idx, box in enumerate(boxes):
                # 5. 책등 크롭 (detector.py)
                cropped_img = crop_spine(img, box, masks, idx)
                
                # 6. OCR 모델(Gemma) 전달을 위해 이미지를 Base64로 인코딩
                _, buffer = cv2.imencode('.jpg', cropped_img)
                base64_image = base64.b64encode(buffer).decode('utf-8')
                
                # 7. 텍스트 추출 (ocr.py)
                ocr_result = extract_text_with_gemma(base64_image)
                ocr_call_number = ocr_result.get("call_number", "")
                ocr_title = ocr_result.get("title", "")

                # 정상적으로 인식된 경우에만 매칭 시도
                if ocr_call_number and "인식실패" not in ocr_call_number:
                    # 8. 도서 매칭 (matcher.py - 1단계 & 2단계 하이브리드)
                    candidates = get_top_candidates(db, ocr_call_number)
                    best_match = hybrid_book_matching_with_jamo(ocr_call_number, ocr_title, candidates)
                    
                    if best_match:
                        raw_books.append({
                            "title": best_match.title,
                            "call_number": best_match.call_number,
                            "shelf_location": getattr(best_match, "assigned_loc_id", "미지정 구역")
                        })
                    else:
                        # 매칭 실패 시 OCR 결과만라도 저장
                        raw_books.append({
                            "title": ocr_title if ocr_title else "알 수 없는 도서",
                            "call_number": ocr_call_number,
                            "shelf_location": "위치 파악 불가"
                        })

        # 9. 청구기호 기반 동선 정렬 (cart_sorter.py)
        sorted_books = CartSorter.sort_by_call_number(raw_books)

        # 10. 결과 DB 저장
        for index, book in enumerate(sorted_books):
            item = CartItem(
                session_id=session_id,
                title=book["title"],
                call_number=book["call_number"],
                shelf_location=book["shelf_location"],
                display_order=index + 1
            )
            db.add(item)

        session.status = "SUCCESS"
        db.commit()

    except Exception as e:
        db.rollback()
        session = db.query(CartSession).filter(CartSession.id == session_id).first()
        if session:
            session.status = "FAILED"
            db.commit()
        print(f"[ERROR] Cart Pipeline processing failed: {str(e)}")
        
    finally:
        db.close()
        # 11. 임시 파일 삭제
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
