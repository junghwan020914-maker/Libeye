# ... 기존 import 유지
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# 1. Library_Master (위치/서가 마스터)
class LibraryMaster(Base):
    __tablename__ = 'library_master'

    location_id = Column(String(50), primary_key=True)
    floor = Column(Integer, nullable=False)
    room_name = Column(String(100), nullable=False)
    section = Column(String(20), nullable=False)
    shelf_num = Column(Integer, nullable=False)
    level_num = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

# 2. Book_Master (도서 마스터)
class BookMaster(Base):
    __tablename__ = 'book_master'

    book_id = Column(String(50), primary_key=True)
    barcode = Column(String(50), unique=True)
    call_number = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(100))
    assigned_loc_id = Column(String(50), ForeignKey('library_master.location_id'))
    # 🚨 [추가해야 할 부분] 서가 내 올바른 순서 (오배열 판별용)
    expected_order = Column(Integer)

# 3. Scan_Session (AI 분석 세션 관리 - 칸 단위 '그룹'으로 변경)
class ScanSession(Base):
    __tablename__ = 'scan_session'

    session_id = Column(String(50), primary_key=True)
    location_id = Column(String(50), ForeignKey('library_master.location_id'), nullable=True)

    status = Column(String(20), default='PENDING')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # 🚨 [추가됨] 수정 발생 시 시간을 추적하기 위한 컬럼
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    total_books = Column(Integer, default=0)
    misplaced_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)
    inferred_location_id = Column(String(50), nullable=True)

    images = relationship("ScanImage", back_populates="session", cascade="all, delete-orphan")
    results = relationship("ScanResultDetail", back_populates="session", cascade="all, delete-orphan")

# 🚨 3-1. [신규 추가] Scan_Image (하나의 세션에 속한 여러 장의 조각 사진 관리)
class ScanImage(Base):
    __tablename__ = 'scan_image'

    image_id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('scan_session.session_id', ondelete='CASCADE'), index=True)
    image_url = Column(String(255), nullable=False)

    # 해당 칸에서 왼쪽부터 찍은 사진의 순서 (0, 1, 2...)
    sequence_order = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False)

    # 양방향 관계 설정
    session = relationship("ScanSession", back_populates="images")
    results = relationship("ScanResultDetail", back_populates="source_image")

class ScanResultDetail(Base):
    __tablename__ = 'scan_result_detail'

    detection_id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('scan_session.session_id'), index=True)
    source_image_id = Column(String(50), ForeignKey('scan_image.image_id', ondelete='SET NULL'), nullable=True)
    bounding_box = Column(JSONB)

    raw_ocr_title = Column(String(255))
    raw_ocr_call_number = Column(String(100))
    matched_book_id = Column(String(50), ForeignKey('book_master.book_id'), nullable=True)

    detected_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    
    # 🚨 [추가됨] 프론트엔드에서 오배열 확인(조치)을 완료했는지 여부
    is_verified = Column(Boolean, default=False)

    # 🌟 [신규 추가] 조치 방법 기록 ('MANUAL': 개별 확인, 'BATCH_OVERWRITE': 일괄 강제 완료)
    verification_method = Column(String(20), nullable=True)

    confidence = Column(Integer, default=0)
    crop_image_url = Column(String(255), nullable=True)

    session = relationship("ScanSession", back_populates="results")
    source_image = relationship("ScanImage", back_populates="results")
    book = relationship("BookMaster")

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
