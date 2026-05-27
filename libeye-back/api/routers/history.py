from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import ScanSession, ScanResultDetail
from typing import Optional

router = APIRouter(prefix="/api/v1/sessions/history", tags=["History"])

@router.get("")
def get_history(location_id: Optional[str] = None, db: Session = Depends(get_db)):
    # 기본 쿼리 생성
    query = db.query(ScanSession)
    
    # location_id가 전달된 경우 필터링 추가
    if location_id:
        query = query.filter(ScanSession.location_id == location_id)
        
    # 정렬 및 50개 제한
    sessions = query.order_by(desc(ScanSession.created_at)).limit(50).all()
    
    history = []
    for session in sessions:
        results = db.query(ScanResultDetail).filter(ScanResultDetail.session_id == session.session_id).all()
        total_count = len(results)
        error_count = sum(1 for r in results if r.status not in ["MATCH", "PENDING"] and not r.is_verified)

        # 2. [신규 추가] 결과 중 하나라도 일괄 조치(BATCH_OVERWRITE)로 처리된 이력이 있는지 확인
        has_batch_action = any(r.verification_method == 'BATCH_OVERWRITE' for r in results)

        history.append({
            "session_id": session.session_id,
            "location_id": session.location_id,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "total_count": total_count,
            "error_count": error_count,
            "has_batch_action": has_batch_action
        })
    return history
