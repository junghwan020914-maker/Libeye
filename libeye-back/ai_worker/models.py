from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
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

# 3. Scan_Session (AI 분석 세션 관리)
class ScanSession(Base):
    __tablename__ = 'scan_session'
    
    session_id = Column(String(50), primary_key=True)
    location_id = Column(String(50), ForeignKey('library_master.location_id'), nullable=True)
    image_url = Column(String(255))
    status = Column(String(20), default='PENDING') # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_image_deleted = Column(Boolean, default=False)
    
    results = relationship("ScanResultDetail", back_populates="session")

# 4. Scan_Result_Detail (YOLO + VLM 분석 결과 저장)
class ScanResultDetail(Base):
    __tablename__ = 'scan_result_detail'
    
    detection_id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('scan_session.session_id'), index=True)
    bounding_box = Column(JSONB)
    ocr_text = Column(String(255))
    matched_book_id = Column(String(50), ForeignKey('book_master.book_id'), nullable=True)
    status = Column(String(20)) # MATCH, MISPLACED, MISSING
    confidence = Column(Integer, default=0)

    session = relationship("ScanSession", back_populates="results")
