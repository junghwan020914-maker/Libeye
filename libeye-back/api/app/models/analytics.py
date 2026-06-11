from sqlalchemy import Column, Integer, DateTime, Date
from sqlalchemy.sql import func
from app.database import Base

# 5. Daily_Analytics (날짜별 집계 캐시 - 주간 차트용)
class DailyAnalytics(Base):
    __tablename__ = 'daily_analytics'

    date = Column(Date, primary_key=True)
    total_scans = Column(Integer, default=0)               # 해당 날 총 인식 책 권수
    misplaced_count = Column(Integer, default=0)           # 오배열 수 (MISPLACED)
    unknown_count = Column(Integer, default=0)             # 인식 실패 수 (UNKNOWN)
    session_count = Column(Integer, default=0)             # 완료된 세션 수
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# 6. Analytics_Total (전체 누적 집계 - 오류비율/AI성공률용, 항상 id=1 단일 행)
class AnalyticsTotal(Base):
    __tablename__ = 'analytics_total'

    id = Column(Integer, primary_key=True, default=1)
    total_scans = Column(Integer, default=0)               # 전체 누적 인식 책 권수
    misplaced_count = Column(Integer, default=0)           # 전체 누적 오배열 수 (MISPLACED)
    unknown_count = Column(Integer, default=0)             # 전체 누적 인식 실패 수 (UNKNOWN)
    session_count = Column(Integer, default=0)             # 전체 누적 세션 수
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
