from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import ScanSession, ScanResultDetail

router = APIRouter(prefix="/api/v1/sessions/history", tags=["History"])

@router.get("")
def get_history(db: Session = Depends(get_db)):
    sessions = db.query(ScanSession).order_by(desc(ScanSession.created_at)).limit(50).all()
    history = []
    for session in sessions:
        results = db.query(ScanResultDetail).filter(ScanResultDetail.session_id == session.session_id).all()
        total_count = len(results)
        error_count = sum(1 for r in results if r.status not in ["MATCH", "PENDING"])
        
        history.append({
            "session_id": session.session_id,
            "location_id": session.location_id,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "total_count": total_count,
            "error_count": error_count,
        })
    return history
