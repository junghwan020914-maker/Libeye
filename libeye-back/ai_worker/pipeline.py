import base64
import cv2

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, DATABASE_URL
from storage import s3_client, ensure_buckets_exist, upload_image, download_image
from service.detector import yolo_model, run_detection, crop_spine
from service.ocr import extract_text_with_gemma
from service.matcher import match_book_by_call_number
from service.misplacement import detect_misplacements
from models import ScanSession, ScanResultDetail

# --- 앱 초기화 ---
celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ensure_buckets_exist()


# --- 메인 파이프라인 ---

@celery_app.task(name="process_image_task")
def process_scan_session(session_id: str, original_file_name: str):
    if yolo_model is None:
        return {"status": "error", "message": "YOLO model not loaded"}

    db = SessionLocal()
    session = None
    scanned_results = []

    try:
        session = db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
        if session:
            session.status = "PROCESSING"
            db.commit()

        # 1. MinIO에서 원본 이미지 다운로드
        print(f"[{session_id}] 1. 원본 이미지 다운로드")
        img = download_image("original-bucket", original_file_name)
        if img is None:
            raise RuntimeError(f"이미지 다운로드 실패: {original_file_name}")

        # 2. YOLO 탐지
        print(f"[{session_id}] 2. YOLO 탐지")
        boxes, masks = run_detection(img)

        if boxes is None or len(boxes) == 0:
            print(f"[{session_id}] 탐지된 책 없음")
        else:
            print(f"[{session_id}] {len(boxes)}권 탐지")

            for idx, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # 3. 마스크 크롭 + MinIO 업로드
                crop_img = crop_spine(img, box, masks, idx)
                crop_key = f"{session_id}_crop_{idx}.jpg"
                crop_url = upload_image("crop-bucket", crop_key, crop_img)

                # 4. Gemma OCR
                _, buf = cv2.imencode(".jpg", crop_img)
                b64 = base64.b64encode(buf).decode("utf-8")
                print(f"[{session_id}] OCR 요청 중 (crop {idx})")
                ocr_result = extract_text_with_gemma(b64)

                # 5. DB 퍼지 매칭
                raw_call_number = ocr_result.get("call_number", "")
                matched = match_book_by_call_number(db, raw_call_number, session.location_id)

                scanned_results.append({
                    "bounding_box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
                    "raw_ocr_data": ocr_result,
                    "matched_book_id":  matched.book_id         if matched else None,
                    "assigned_loc_id":  matched.assigned_loc_id if matched else None,
                    "expected_order":   matched.expected_order  if matched else None,
                    "confidence": int(box.conf[0] * 100),
                    "crop_url": crop_url,
                })

        # 6. x 좌표 정렬 + 오배열 판별
        print(f"[{session_id}] 6. 오배열 판별")
        scanned_results.sort(key=lambda r: r["bounding_box"]["x"])
        final_results = detect_misplacements(scanned_results, session.location_id if session else None)

        # 7. DB 저장
        print(f"[{session_id}] 7. 결과 저장")
        for idx, result in enumerate(final_results):
            ocr = result.get("raw_ocr_data", {})
            db.add(ScanResultDetail(
                detection_id=f"{session_id}-det-{idx}",
                session_id=session_id,
                bounding_box=result["bounding_box"],
                raw_ocr_title=ocr.get("title", ""),
                raw_ocr_call_number=ocr.get("call_number", ""),
                matched_book_id=result["matched_book_id"],
                detected_order=idx + 1,
                status=result["status"],
                confidence=result["confidence"],
                crop_image_url=result.get("crop_url"),
            ))

        if session:
            session.status = "COMPLETED"
        db.commit()

        print(f"[{session_id}] 파이프라인 완료")
        return {"status": "success", "session_id": session_id}

    except Exception as e:
        db.rollback()
        if session:
            session.status = "FAILED"
            db.commit()
        print(f"[{session_id}] 오류: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        db.close()
