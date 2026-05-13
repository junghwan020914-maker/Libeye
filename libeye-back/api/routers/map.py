from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import ScanSession, ScanResultDetail, LibraryMaster

router = APIRouter(prefix="/api/v1/map", tags=["Map"])

@router.get("/status")
def get_map_status(db: Session = Depends(get_db)):
    locations = db.query(LibraryMaster).filter(LibraryMaster.is_active == True).all()
    status_dict = {}
    
    for loc in locations:
        latest_session = db.query(ScanSession).filter(ScanSession.location_id == loc.location_id).order_by(desc(ScanSession.created_at)).first()
        if not latest_session:
            status_dict[loc.location_id] = {"status": "pending", "error_count": 0}
        else:
            if latest_session.status != "COMPLETED":
                status_dict[loc.location_id] = {"status": "pending", "error_count": 0}
            else:
                errors = db.query(ScanResultDetail).filter(
                    ScanResultDetail.session_id == latest_session.session_id,
                    ScanResultDetail.status != "MATCH"
                ).count()
                
                if errors > 0:
                    status_dict[loc.location_id] = {"status": "error", "error_count": errors}
                else:
                    status_dict[loc.location_id] = {"status": "done", "error_count": 0}
                    
    return status_dict
