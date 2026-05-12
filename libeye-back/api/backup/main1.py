from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from typing import Dict, Any

# 향후 모듈 분리를 고려하여 storage 모듈 임포트
from storage import get_presigned_upload_url, get_presigned_download_url

app = FastAPI(
    title="LibEye API Server",
    description="스마트 서고 관리 시스템 (On-Premises 최적화) API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 태블릿/모바일 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 운영 환경에서는 실제 프론트엔드 도메인/IP로 제한해야 합니다.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [Pydantic DTO 모델 정의] ---
class SessionCreateRequest(BaseModel):
    location_id: str
    user_id: str

class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    
class UploadUrlResponse(BaseModel):
    upload_url: str
    expires_in: int

# --- [API 라우터] ---

@app.get("/")
async def root():
    return {"message": "LibEye API 서버가 정상적으로 실행 중입니다."}

@app.post("/api/v1/sessions", response_model=SessionCreateResponse, status_code=201)
async def create_session(request: SessionCreateRequest):
    """
    1. 스캔 세션 생성: 특정 서가를 스캔하기 위한 논리적 세션을 엽니다.
    (실제로는 여기서 PostgreSQL DB의 Scan_Session 테이블에 INSERT 합니다.)
    """
    new_session_id = str(uuid.uuid4())
    
    # TODO: DB 세션 생성 로직 추가 공간
    
    return SessionCreateResponse(
        session_id=new_session_id,
        status="CREATED"
    )

@app.get("/api/v1/sessions/{session_id}/upload-url", response_model=UploadUrlResponse)
async def generate_upload_url(session_id: str = Path(..., description="스캔 세션 UUID")):
    """
    2. MinIO Presigned URL 발급: 파일을 API 서버를 거치지 않고 MinIO 스토리지로 직접 업로드하기 위한 주소 발급
    """
    # 저장될 객체명 생성 (예: sessions/123e4567-.../original.jpg)
    object_name = f"sessions/{session_id}/original.jpg"
    
    try:
        upload_url = get_presigned_upload_url("original-bucket", object_name)
        return UploadUrlResponse(
            upload_url=upload_url,
            expires_in=300 # 5분 (300초)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 URL 생성 실패: {str(e)}")

@app.get("/api/v1/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    3. 분석 상태 폴링 (Polling): AI 워커의 처리 상태를 반환합니다.
    """
    # TODO: Redis 또는 DB에서 현재 진행 상태를 조회하는 로직
    return {
        "session_id": session_id,
        "status": "PROCESSING", 
        "queue_position": 2, 
        "message": "현재 다른 스캔 작업을 처리 중입니다. 잠시만 기다려주세요."
    }

@app.get("/api/v1/sessions/{session_id}/results")
async def get_session_results(session_id: str):
    """
    4. 분석 결과 및 로컬 이미지 경로 반환
    """
    # 원본 이미지 다운로드/열람용 URL 생성 (UI 표시용)
    object_name = f"sessions/{session_id}/original.jpg"
    image_url = get_presigned_download_url("original-bucket", object_name)
    
    # TODO: DB의 Scan_Result_Detail 테이블에서 결과 조회
    return {
        "session_id": session_id,
        "image_url": image_url,
        "detections": [
            {
                "detection_id": str(uuid.uuid4()),
                "bounding_box": {"x": 120, "y": 300, "w": 45, "h": 280},
                "ocr_text": "813.6 김12가",
                "matched_book_id": "BOOK-88219",
                "status": "MATCH"
            }
        ]
    }
