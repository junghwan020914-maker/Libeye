from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import os
import re

# 수정됨: api. 접두사 제거 (컨테이너 내에서는 api 폴더 안의 파일들이 최상위 경로임)
from database import get_db 
from models import ScanSession, ScanResultDetail

router = APIRouter(prefix="/api/v1/sessions", tags=["Results"])

# MinIO 내부 URL 패턴: http://minio:9000/{bucket}/{key}
_MINIO_URL_PATTERN = re.compile(r"https?://[^/]+/([^/]+)/(.+)")

def _to_proxy_url(request: Request, minio_url: str) -> str:
    """
    MinIO 내부 URL (http://minio:9000/bucket/key)을
    FastAPI 프록시 URL (/api/v1/image-proxy/bucket/key)로 변환합니다.
    브라우저가 ngrok을 직접 거치지 않아도 됩니다.
    """
    if not minio_url:
        return minio_url
    
    m = _MINIO_URL_PATTERN.match(minio_url)
    if not m:
        return minio_url
    
    bucket, key = m.group(1), m.group(2)
    # FastAPI의 실제 요청 base_url을 기반으로 프록시 URL 생성
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/image-proxy/{bucket}/{key}"

@router.get("/{session_id}/results")
async def get_scan_results(session_id: str, request: Request, db: Session = Depends(get_db)):
    """
    대시보드 또는 AR 클라이언트에서 분석 완료 결과를 조회하는 API.
    이미지 URL은 FastAPI 프록시를 통해 제공되므로 MinIO/ngrok에 직접 접근하지 않습니다.
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
            "ocr_title": r.raw_ocr_title,
            "ocr_call_number": r.raw_ocr_call_number,
            "status": r.status,
            "matched_book_id": r.matched_book_id,
            # MinIO URL → FastAPI 프록시 URL로 변환
            "crop_image_url": _to_proxy_url(request, r.crop_image_url),
            "confidence": r.confidence
        })
    
    return {
        "session_id": session_id,
        "image_url": _to_proxy_url(request, session_info.image_url),
        "status": session_info.status,
        "detections": detections
    }
