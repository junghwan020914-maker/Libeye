import os
import uuid
import json
import base64
import cv2
import numpy as np
import requests
import boto3
from urllib.request import urlopen
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- PyTorch 2.6+ 보안 정책(weights_only) 환경 변수 차단 ---
os.environ['TORCH_WEIGHTS_ONLY'] = '0'
import torch

_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO

# DB 모델 임포트
from models import ScanSession, ScanResultDetail

# --- 환경 설정 ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:capstone123@postgres:5432/capstone_db")
OLLAMA_API_URL = "http://ollama:11434/api/generate"

# [중요] 실제 다운로드된 모델 이름으로 맞춰주세요. (예: gemma, gemma:7b, llama3 등)
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma4:26b") 

# --- MinIO (S3) 스토리지 설정 ---
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin1234"

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY
)

celery_app = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- AI 모델 초기화 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'weights', 'best.pt')

try:
    print(f"Loading YOLO model from {YOLO_MODEL_PATH}...")
    yolo_model = YOLO(YOLO_MODEL_PATH, task='segment') 
    print("✅ YOLO model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    yolo_model = None

# --- 버킷 초기화 함수 ---
def ensure_buckets_exist():
    try:
        buckets = [b['Name'] for b in s3_client.list_buckets()['Buckets']]
        if 'original-bucket' not in buckets:
            s3_client.create_bucket(Bucket='original-bucket')
        if 'crop-bucket' not in buckets:
            s3_client.create_bucket(Bucket='crop-bucket')
    except Exception as e:
        print(f"MinIO 연동 오류 (무시하고 진행): {e}")

ensure_buckets_exist()


# --- 유틸리티 함수 ---

def upload_to_minio(bucket_name, file_name, cv2_img):
    try:
        _, buffer = cv2.imencode('.jpg', cv2_img)
        img_bytes = buffer.tobytes()
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=img_bytes,
            ContentType='image/jpeg'
        )
        return f"{MINIO_ENDPOINT}/{bucket_name}/{file_name}"
    except Exception as e:
        print(f"S3 Upload Error: {e}")
        return None

def load_image(image_data):
    if image_data.startswith('data:image'):
        encoded_data = image_data.split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return None

def extract_text_with_gemma(base64_image):
    prompt = """
    You are a library assistant. Examine the image of the book spine.
    Extract the 'call_number' (e.g., 813.6 김12가) and the 'title'.
    Respond strictly in JSON format like this:
    {"call_number": "extracted text", "title": "extracted text"}
    If you cannot read it, return empty strings.
    """
    payload = {
        "model": OLLAMA_MODEL_NAME, 
        "prompt": prompt,
        "images": [base64_image],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
    }
    try:
        # [수정됨] 26B 같은 거대 모델의 최초 로딩(Cold Start) 시간을 고려하여 
        # timeout을 40초에서 300초(5분)로 대폭 늘립니다.
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300) 
        
        if response.status_code == 404:
            print(f"❌ [Ollama Error] '{OLLAMA_MODEL_NAME}' 모델을 찾을 수 없습니다.")
            return {"call_number": "인식실패(모델없음)", "title": "인식실패"}
            
        response.raise_for_status()
        return json.loads(response.json().get('response', '{}'))
    except Exception as e:
        print(f"Gemma OCR Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response details: {e.response.text}")
        return {"call_number": "인식실패(통신오류)", "title": "인식실패"}

def calculate_lis_misplacement(scanned_books):
    if not scanned_books: return []
    scanned_books.sort(key=lambda x: x['bounding_box']['x'])
    call_numbers = [book['extracted_call_number'] for book in scanned_books]
    
    n = len(call_numbers)
    lis_length = [1] * n
    prev_index = [-1] * n
    
    for i in range(1, n):
        for j in range(0, i):
            if call_numbers[j] < call_numbers[i] and lis_length[i] < lis_length[j] + 1:
                lis_length[i] = lis_length[j] + 1
                prev_index[i] = j
                
    max_len = max(lis_length) if lis_length else 0
    max_idx = lis_length.index(max_len) if max_len > 0 else -1
    
    correct_sequence_indices = set()
    while max_idx >= 0:
        correct_sequence_indices.add(max_idx)
        max_idx = prev_index[max_idx]
        
    for i, book in enumerate(scanned_books):
        book['status'] = 'MATCH' if i in correct_sequence_indices else 'MISPLACED'
        
    return scanned_books


# --- 메인 파이프라인 ---

@celery_app.task(name="process_image_task")
def process_scan_session(session_id, original_file_name): # 파라미터 이름 변경
    if yolo_model is None:
        return {"status": "error", "message": "YOLO model not loaded"}

    db = SessionLocal()
    scanned_results = []
    
    try:
        session = db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
        if session:
            session.status = "PROCESSING"
            db.commit()

        print(f"[{session_id}] 1. MinIO에서 원본 이미지 다운로드...")
        
        # --- [추가] MinIO에서 파일 가져와서 OpenCV 이미지로 변환 ---
        response = s3_client.get_object(Bucket='original-bucket', Key=original_file_name)
        image_bytes = response['Body'].read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        print(f"[{session_id}] 2. YOLO 추론 시작...")
        results = yolo_model(img, conf=0.5) 
        
        boxes = results[0].boxes
        masks = results[0].masks # [수정됨] 마스크 데이터 추출
        
        if boxes is None or len(boxes) == 0:
            print(f"[{session_id}] 탐지된 책이 없습니다.")
        else:
            print(f"[{session_id}] YOLOv8: {len(boxes)}권의 책등 탐지 완료.")

            for idx, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                
                # --- [핵심 수정됨] 마스크(누끼) 영역 외 배경을 검은색으로 칠하기 ---
                if masks is not None and len(masks.xy) > idx:
                    mask_pts = masks.xy[idx] # 다각형 좌표
                    
                    # 원본 이미지와 똑같은 크기의 새카만 캔버스 생성
                    black_bg = np.zeros_like(img)
                    
                    # 캔버스에 책등 영역만 흰색(255) 다각형으로 칠하기
                    cv2.fillPoly(black_bg, [np.int32(mask_pts)], (255, 255, 255))
                    
                    # 원본 이미지와 AND 연산 (책등은 남고, 나머지는 완벽한 검은색으로 덮임)
                    segmented_img = cv2.bitwise_and(img, black_bg)
                    
                    # 칠해진 이미지에서 네모 반듯하게 크롭
                    crop_img = segmented_img[y1:y2, x1:x2]
                else:
                    # 마스크가 없으면 기존처럼 단순 크롭
                    crop_img = img[y1:y2, x1:x2]
                # ----------------------------------------------------------------

                crop_file_name = f"{session_id}_crop_{idx}.jpg"
                crop_url = upload_to_minio('crop-bucket', crop_file_name, crop_img)
                print(f"  - Crop 저장(배경 블랙 처리됨): {crop_file_name}")
                
                _, buffer = cv2.imencode('.jpg', crop_img)
                base64_image = base64.b64encode(buffer).decode('utf-8')
                
                print(f"  - Gemma OCR 요청 중... (Crop {idx})")
                vlm_data = extract_text_with_gemma(base64_image)
                
                scanned_results.append({
                    "bounding_box": {"x": x1, "y": y1, "w": w, "h": h},
                    "extracted_call_number": vlm_data.get("call_number", ""),
                    "extracted_title": vlm_data.get("title", ""),
                    "confidence": int(box.conf[0] * 100),
                    "crop_url": crop_url 
                })
            
        print(f"[{session_id}] 4. LIS 알고리즘 기반 오배열 판별 중...")
        final_results = calculate_lis_misplacement(scanned_results)
        
        print(f"[{session_id}] 5. 분석 결과 DB 저장 중...")
        for idx, result in enumerate(final_results):
            det_id = f"{session_id}-det-{idx}"
            new_detail = ScanResultDetail(
                detection_id=det_id,
                session_id=session_id,
                bounding_box=result["bounding_box"],
                ocr_text=result["extracted_call_number"],
                status=result["status"],
                confidence=result["confidence"]
            )
            db.add(new_detail)
        
        if session:
            session.status = "COMPLETED"
            
        db.commit()
        print(f"[{session_id}] 🎉 모든 파이프라인 처리 완료 (웹 대시보드로 결과 송출)!")
        return {"status": "success", "session_id": session_id}

    except Exception as e:
        db.rollback()
        if session:
            session.status = "FAILED"
            db.commit()
        print(f"[{session_id}] ❌ 처리 중 오류 발생: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
