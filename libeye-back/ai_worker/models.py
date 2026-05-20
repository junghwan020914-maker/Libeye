from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 수정됨: .database 대신 database로 직접 임포트
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

    # 🚨 수정: 다중 이미지를 위해 기존 단일 image_url, is_image_deleted 삭제
    status = Column(String(20), default='PENDING') # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 세션 완료 시 파이프라인이 채워주는 집계 컬럼
    total_books = Column(Integer, default=0)               # YOLO가 탐지한 총 책 권수
    misplaced_count = Column(Integer, default=0)           # 오배열 책 수 (MISPLACED)
    unknown_count = Column(Integer, default=0) # 인식 실패 수 (UNKNOWN)

    # 🚨 수정: 세션 삭제 시 연관된 스캔 이미지와 결과 데이터가 모두 삭제되도록 cascade 설정
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

# 4. Scan_Result_Detail (YOLO + VLM 분석 결과 및 보정 데이터 저장)
class ScanResultDetail(Base):
    __tablename__ = 'scan_result_detail'

    detection_id = Column(String(50), primary_key=True)

    # 해당 스캔 세션 연결
    session_id = Column(String(50), ForeignKey('scan_session.session_id'), index=True)

    # 🚨 [추가됨] 병합 과정에서 이 도서 객체가 주로 어느 이미지에서 추출되었는지 추적
    source_image_id = Column(String(50), ForeignKey('scan_image.image_id', ondelete='SET NULL'), nullable=True)

    # 책등 좌표
    bounding_box = Column(JSONB)

    # 1. AI 원본 데이터 (Gemma4가 추출한 책 제목, 청구기호 통째로 저장)
    raw_ocr_title = Column(String(255))        # AI가 읽은 원본 제목
    raw_ocr_call_number = Column(String(100))  # AI가 읽은 원본 청구기호

    # 2. 보정된 정답 데이터 연결 (DB Master 연동)
    matched_book_id = Column(String(50), ForeignKey('book_master.book_id'), nullable=True)

    # 🚨 [유지/중요] 여러 장의 사진을 중복 제거하고 병합한 후의 '해당 칸(Shelf) 전체 기준 물리적 최종 순서'
    detected_order = Column(Integer, nullable=False)

    # 최종 상태 (MATCH, MISPLACED, EXTRA, UNKNOWN, PENDING)
    status = Column(String(20), nullable=False, default="PENDING")

    # AI 인식 신뢰도 점수
    confidence = Column(Integer, default=0)

    crop_image_url = Column(String(255), nullable=True)

    # 🚨 수정: 양방향 관계(Relationship) 설정 업데이트
    session = relationship("ScanSession", back_populates="results")
    source_image = relationship("ScanImage", back_populates="results") # 추가됨
    book = relationship("BookMaster") # 매칭된 도서 객체에 ORM으로 바로 접근 가능


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
