from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

# 수정됨: api. 접두사 제거 (컨테이너 내에서는 api 폴더 안의 파일들이 최상위 경로임)
from database import get_db 
from models import ScanSession, ScanResultDetail

router = APIRouter(prefix="/api/v1/sessions", tags=["Results"])

# MinIO 내부 주소 → 외부 접근 가능한 URL로 교체 (ngrok 터널 URL)
MINIO_INTERNAL = "http://minio:9000"
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "").rstrip("/")

def _to_public_url(url: str) -> str:
    """MinIO 내부 URL을 외부에서 접근 가능한 URL로 변환합니다."""
    if not url or not MINIO_PUBLIC_URL:
        return url
    # http://minio:9000/... → https://xxxx.ngrok-free.app/...
    return url.replace(MINIO_INTERNAL, MINIO_PUBLIC_URL)

@router.get("/{session_id}/results")
async def get_scan_results(session_id: str, db: Session = Depends(get_db)):
    """
    대시보드 또는 AR 클라이언트에서 분석 완료 결과를 조회하는 API.
    """
    session_info = db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
    
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_info.status != "COMPLETED":
        return {
            "session_id": session_id,
            "status": session_info.status,
            "message": "AI analysis is not completed yet."
        }
        
    results = db.query(ScanResultDetail).filter(ScanResultDetail.session_id == session_id).all()
    
    detections = []
    for r in results:
        detections.append({
            "detection_id": r.detection_id,
            "bounding_box": r.bounding_box,
            
            # 🚨 수정: 새로운 컬럼에서 직접 데이터를 가져옴
            "ocr_title": r.raw_ocr_title,
            "ocr_call_number": r.raw_ocr_call_number,
            
            "status": r.status,
            "matched_book_id": r.matched_book_id,
            # 내부 MinIO URL → ngrok 공개 URL로 변환
            "crop_image_url": _to_public_url(r.crop_image_url),
            "confidence": r.confidence
        })
    
    return {
        "session_id": session_id,
        "image_url": _to_public_url(session_info.image_url),
        "status": session_info.status,
        "detections": detections
    }
