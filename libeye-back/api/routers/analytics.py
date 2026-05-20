from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import DailyAnalytics, AnalyticsTotal
from datetime import date, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_analytics_dashboard(db: Session = Depends(get_db)):
    # ── 주간 서가 점검량 (DailyAnalytics) ──────────────────────────────────
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(6)]  # 월~토

    daily_records = (
        db.query(DailyAnalytics)
        .filter(DailyAnalytics.date.in_(week_dates))
        .all()
    )
    daily_map = {r.date: r for r in daily_records}
    weekly_scans = [
        (daily_map[d].total_scans if d in daily_map else 0)
        for d in week_dates
    ]

    # ── 오류 비율 / AI 성공률 (AnalyticsTotal - 전체 누적) ─────────────────
    total_row = db.query(AnalyticsTotal).filter(AnalyticsTotal.id == 1).first()

    if total_row and total_row.total_scans:
        misplaced = total_row.misplaced_count or 0
        unknown   = total_row.unknown_count or 0
        total     = total_row.total_scans
        # AI 성공률: 탐지된 책 중 인식 실패(UNKNOWN)를 제외한 비율
        ai_success_rate = round((total - unknown) / total * 100)
    else:
        misplaced = unknown = 0
        ai_success_rate = 0

    return {
        "weekly_scans": weekly_scans,
        "error_ratios": {
            "MISPLACED": misplaced,
            "UNKNOWN":   unknown,
        },
        "ai_success_rate": ai_success_rate,
    }
