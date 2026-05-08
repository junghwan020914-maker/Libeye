from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 수정됨: api. 접두사 제거 (컨테이너 내에서는 api 폴더 안의 파일들이 최상위 경로임)
from database import get_db 
from models import ScanSession, ScanResultDetail

router = APIRouter(prefix="/api/v1/sessions", tags=["Results"])

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
            # 🚨 [수정된 부분] 프론트엔드로 URL 전달
            "crop_image_url": r.crop_image_url,
            "confidence": r.confidence
        })
    
    return {
        "session_id": session_id,
        "image_url": session_info.image_url,
        "status": session_info.status,
        "detections": detections
    }
