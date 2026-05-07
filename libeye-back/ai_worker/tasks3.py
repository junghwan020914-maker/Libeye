import os
import cv2
import numpy as np
from celery import Celery
from ultralytics import YOLO
from .database import SessionLocal
from .models import ScanSession, ScanResultDetail
from .storage import upload_file_to_minio, download_file_from_minio # storage.py 필요

# Celery 설정
celery_app = Celery('libeye_worker', broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))

# 1. 모델 로드 (컨테이너 시작 시 한 번만 로드하여 VRAM 절약)
MODEL_PATH = 'weights/best.pt'
model = YOLO(MODEL_PATH)

@celery_app.task(name="process_scan_image")
def process_scan_image(session_id: str, image_name: str):
    db = SessionLocal()
    try:
        # 1. MinIO에서 원본 이미지 다운로드 [cite: 10]
        local_input_path = f"/tmp/{image_name}"
        download_file_from_minio("original-bucket", image_name, local_input_path)
        
        img = cv2.imread(local_input_path)
        if img is None:
            raise ValueError("이미지를 불러올 수 없습니다.")

        # 2. YOLO 추론 (conf threshold 0.5)
        results = model(img, conf=0.5)
        
        detected_books = []
        
        for i, result in enumerate(results):
            if result.masks is not None:
                masks = result.masks.data.cpu().numpy()
                boxes = result.boxes.xyxy.cpu().numpy()
                
                for j, (mask, box) in enumerate(zip(masks, boxes)):
                    # 마스크 기반 책등 분리 (tester.py 로직)
                    mask_resized = cv2.resize(mask, (img.shape[1], img.shape[0]))
                    mask_binary = (mask_resized > 0.5).astype(np.uint8)
                    mask_3ch = np.stack([mask_binary] * 3, axis=-1)
                    
                    isolated_spine = img * mask_3ch
                    x1, y1, x2, y2 = map(int, box)
                    cropped_spine = isolated_spine[y1:y2, x1:x2]
                    
                    # 3. 잘라낸 책등 이미지 저장 및 MinIO 업로드 
                    crop_filename = f"crop_{session_id}_{i}_{j}.png"
                    local_crop_path = f"/tmp/{crop_filename}"
                    cv2.imwrite(local_crop_path, cropped_spine)
                    
                    upload_file_to_minio("crop-bucket", crop_filename, local_crop_path)
                    
                    # 4. 결과 데이터 생성 (Gemma4 OCR은 현재 더미 텍스트로 대체)
                    detected_books.append({
                        "session_id": session_id,
                        "crop_image_url": crop_filename,
                        "bbox": {"x": x1, "y": y1, "w": x2-x1, "h": y2-y1},
                        "ocr_text": f"TEMP-813.{j}" # 향후 Gemma4 연동 포인트
                    })
                    
                    os.remove(local_crop_path) # 임시 파일 삭제

        # 5. DB 저장 및 LIS 알고리즘 적용 [cite: 220, 221]
        # (이전 단계에서 작성한 match_books_with_db 및 evaluate_lis_algorithm 호출)
        save_results_to_db(db, session_id, detected_books)
        
        # 세션 상태 완료로 변경
        session = db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
        session.status = "COMPLETED"
        db.commit()

    except Exception as e:
        print(f"Error: {e}")
        db.query(ScanSession).filter(ScanSession.session_id == session_id).update({"status": "ERROR"})
        db.commit()
    finally:
        db.close()
        if os.path.exists(local_input_path):
            os.remove(local_input_path)

def save_results_to_db(db, session_id, detected_books):
    for book in detected_books:
        new_detail = ScanResultDetail(
            session_id=session_id,
            bounding_box=book["bbox"],
            ocr_text=book["ocr_text"],
            status="MATCH" # LIS 결과에 따라 추후 변경
        )
        db.add(new_detail)
    db.commit()
