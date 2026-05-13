from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import ScanSession, ScanResultDetail
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_analytics_dashboard(db: Session = Depends(get_db)):
    # Mocked data for dashboard if actual logic is complex
    # You would typically group by date, count statuses etc.
    # We will simulate the values based on existing entries for simplicity.
    
    results = db.query(ScanResultDetail).all()
    total_results = len(results)
    
    error_types = {
        "MISPLACED": 0,
        "MISSING": 0,
        "UNKNOWN": 0,
        "EXTRA": 0
    }
    
    success_count = 0
    
    for r in results:
        if r.status in error_types:
            error_types[r.status] += 1
        elif r.status == "MATCH":
            success_count += 1
            
    # Calculate simple AI success vs manual
    # Here we just treat MATCH as success for now.
    ai_success = 92 # Hardcoded percentage for demo if needed, or derived
    
    weekly_data = [120, 150, 180, 140, 210, 80] # Simulated daily scans
    
    return {
        "weekly_scans": weekly_data,
        "error_ratios": error_types,
        "ai_success_rate": ai_success
    }
