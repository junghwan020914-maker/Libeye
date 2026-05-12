from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import re

# 수정됨: api. 접두사 제거 (컨테이너 내에서는 api 폴더 안의 파일들이 최상위 경로임)
from database import get_db 
from models import ScanSession, ScanResultDetail

router = APIRouter(prefix="/api/v1/sessions", tags=["Results"])

# MinIO 내부 URL 패턴: http://minio:9000/{bucket}/{key}
_MINIO_URL_PATTERN = re.compile(r"https?://[^/]+/([^/]+)/(.+)")

def _to_proxy_path(minio_url: str) -> str | None:
    """
    MinIO 내부 URL (http://minio:9000/bucket/key)을
    프론트엔드 상대 경로 (/api/v1/image-proxy/bucket/key)로 변환합니다.
    
    절대 URL이 아닌 상대 경로를 반환하므로:
    - 브라우저가 현재 접속한 프론트엔드 서버(Vite)를 기준으로 요청
    - Vite 프록시가 /api/* → 백엔드로 자동 전달
    - HTTP/HTTPS 불일치(Mixed Content) 문제 없음
    - 방화벽 포트 막힘 문제 없음
    """
    if not minio_url:
        return None
    m = _MINIO_URL_PATTERN.match(minio_url)
    if not m:
        return minio_url
    bucket, key = m.group(1), m.group(2)
    return f"/api/v1/image-proxy/{bucket}/{key}"

@router.get("/{session_id}/results")
async def get_scan_results(session_id: str, db: Session = Depends(get_db)):
    """
    대시보드 또는 AR 클라이언트에서 분석 완료 결과를 조회하는 API.
    이미지 URL은 상대 경로(/api/v1/image-proxy/...)로 반환되며,
    Vite 개발 서버 프록시가 백엔드로 자동 전달합니다.
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
            # 상대 경로 반환 → Vite 프록시가 자동으로 백엔드로 전달
            "crop_image_url": _to_proxy_path(r.crop_image_url),
            "confidence": r.confidence
        })
    
    return {
        "session_id": session_id,
        "image_url": _to_proxy_path(session_info.image_url),
        "status": session_info.status,
        "detections": detections
    }
