# ... 기존 import 유지
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

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
    # unknown_count는 ocr_failed_count + match_failed_count의 합 (하위 호환/분석 대시보드용으로 유지)
    unknown_count = Column(Integer, default=0)
    # 🌟 [신규 추가] 인식 실패 원인 세분화 통계용 컬럼
    ocr_failed_count = Column(Integer, default=0)    # OCR 자체 실패 (텍스트 추출 불가)
    match_failed_count = Column(Integer, default=0)  # OCR은 됐으나 DB 매칭 실패
    inferred_location_id = Column(String(50), nullable=True)
    elapsed_sec = Column(Float, nullable=True)
    # 🌟 [신규] 소요시간 그룹별 분리 저장 (초)
    yolo_time = Column(Float, nullable=True)  # YOLO 탐지
    ocr_time = Column(Float, nullable=True)   # Gemma OCR (1차 + 2차 재인식)
    io_time = Column(Float, nullable=True)    # 크롭/업로드/다운로드/매칭/판별/DB저장 등 I/O성 작업 합산

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
    # 🌟 [신규 추가] matcher.py가 산출한 최고 매칭 점수 (0~100, 매칭 실패 시에도 최고 점수 저장)
    highest_score = Column(Float, default=0)
    crop_image_url = Column(String(255), nullable=True)

    session = relationship("ScanSession", back_populates="results")
    source_image = relationship("ScanImage", back_populates="results")
    book = relationship("BookMaster")
