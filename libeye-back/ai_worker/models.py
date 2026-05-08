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
    
    # 세션 삭제 시 연관된 ScanResultDetail 기록들도 함께 지워지도록 cascade 설정
    results = relationship("ScanResultDetail", back_populates="session", cascade="all, delete-orphan")

# 4. Scan_Result_Detail (YOLO + VLM 분석 결과 및 보정 데이터 저장)
class ScanResultDetail(Base):
    __tablename__ = 'scan_result_detail'
    
    detection_id = Column(String(50), primary_key=True)

    # 해당 스캔 세션 연결
    session_id = Column(String(50), ForeignKey('scan_session.session_id'), index=True)
    
    # 책등 좌표
    bounding_box = Column(JSONB)

    # 1. AI 원본 데이터 (Gemma4가 추출한 책 제목, 청구기호 통째로 저장)
    # 예: {"title": "나미야 잡화점의 기적", "call_number": "813.6 히15나"}
    raw_ocr_data = Column(JSONB)

    # 2. 보정된 정답 데이터 연결 (DB Master 연동)
    # 이 ID를 통해 BookMaster의 정답 title, call_number를 JOIN해서 가져옵니다.
    matched_book_id = Column(String(50), ForeignKey('book_master.book_id'), nullable=True)

    # 사진 상 왼쪽부터의 물리적 순서 (오배열 판별에 사용)
    detected_order = Column(Integer, nullable=False)
    
     # 최종 상태 (MATCH, MISPLACED, MISSING, EXTRA, UNKNOWN, PENDING)
    status = Column(String(20), nullable=False, default="PENDING")
    
    # AI 인식 신뢰도 점수
    confidence = Column(Integer, default=0)

    # 양방향 관계(Relationship) 설정
    session = relationship("ScanSession", back_populates="results")
    book = relationship("BookMaster") # 매칭된 도서 객체에 ORM으로 바로 접근 가능
