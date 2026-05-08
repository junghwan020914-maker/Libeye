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
            
            # ✅ JSONB 딕셔너리에서 청구기호를 꺼내서 프론트엔드에 전달 (키가 없으면 빈 문자열)
            "ocr_text": r.raw_ocr_data.get("call_number", "") if r.raw_ocr_data else "",
            
            # (선택) 프론트엔드에서 도서명도 쓸 수 있도록 원본 데이터를 통째로 넘겨주셔도 좋습니다.
            "raw_ocr_data": r.raw_ocr_data, 
            
            "status": r.status,
            "matched_book_id": r.matched_book_id
        })
    
    return {
        "session_id": session_id,
        "image_url": session_info.image_url,
        "status": session_info.status,
        "detections": detections
    }
