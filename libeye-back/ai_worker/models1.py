import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# 앞서 생성한 database.py에서 Base 클래스 임포트
from database import Base

class LibraryMaster(Base):
    """위치/서가 마스터 테이블"""
    __tablename__ = 'library_master'
    
    location_id = Column(String(50), primary_key=True, index=True)
    floor = Column(Integer, nullable=False)
    room_name = Column(String(100), nullable=False)
    section = Column(String(20), nullable=False)
    shelf_num = Column(Integer, nullable=False)
    level_num = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class BookMaster(Base):
    """도서 마스터 테이블"""
    __tablename__ = 'book_master'
    
    book_id = Column(String(50), primary_key=True, index=True)
    barcode = Column(String(50), unique=True, index=True)
    call_number = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(100))
    assigned_loc_id = Column(String(50), ForeignKey('library_master.location_id'))
    expected_order = Column(Integer)
    
    # Relationship
    location = relationship("LibraryMaster")

class ScanSession(Base):
    """스캔 세션 로그 테이블"""
    __tablename__ = 'scan_session'
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(String(50), ForeignKey('library_master.location_id'))
    user_id = Column(String(50), nullable=False)
    scan_time = Column(DateTime(timezone=True), server_default=func.now())
    image_url = Column(String(500), nullable=False)
    lux_level = Column(Integer)
    overall_status = Column(String(20), nullable=False) # COMPLETED, NEEDS_ACTION
    is_image_deleted = Column(Boolean, default=False)
    
    # Relationship (세션 삭제 시 하위 결과물도 함께 삭제되도록 cascade 설정)
    location = relationship("LibraryMaster")
    details = relationship("ScanResultDetail", back_populates="session", cascade="all, delete-orphan")

class ScanResultDetail(Base):
    """AI 인식 상세 결과 테이블"""
    __tablename__ = 'scan_result_detail'
    
    detection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('scan_session.session_id', ondelete="CASCADE"))
    matched_book_id = Column(String(50), ForeignKey('book_master.book_id'), nullable=True)
    ocr_text = Column(String(100))
    confidence = Column(DECIMAL(5, 2))
    bounding_box = Column(JSONB) # 프론트엔드로 바로 전달될 {x, y, w, h} 좌표계
    detected_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False) # MATCH, MISPLACED, MISSING, EXTRA, UNKNOWN
    
    # Relationship
    session = relationship("ScanSession", back_populates="details")
    book = relationship("BookMaster")

class ManualCorrection(Base):
    """수동 수정/안전장치 이력 테이블"""
    __tablename__ = 'manual_correction'
    
    correction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    detection_id = Column(UUID(as_uuid=True), ForeignKey('scan_result_detail.detection_id'))
    user_id = Column(String(50), nullable=False)
    corrected_book_id = Column(String(50), ForeignKey('book_master.book_id'))
    correction_time = Column(DateTime(timezone=True), server_default=func.now())
    action_type = Column(String(50), nullable=False) # TEXT_FIX, BARCODE_MATCH, MERGED, SPLIT
    
    # Relationship
    detection = relationship("ScanResultDetail")
    corrected_book = relationship("BookMaster")
