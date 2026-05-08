-- 1. 확장 모듈 활성화
-- UUID 생성을 위한 확장 (필요 시 DB 기본값으로 활용)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- OCR 텍스트(청구기호)의 Fuzzy Matching(유사도 검색) 성능을 극대화하기 위한 Trigram 확장
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- 퍼지 매칭(Levenshtein 거리 계산) 활성화
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- 2. 마스터 테이블 생성

-- 2.1 위치/서가 마스터 테이블 (Library_Master)
CREATE TABLE Library_Master (
    location_id VARCHAR(50) PRIMARY KEY, -- 예: LOC-A-2-3
    floor INT NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    section VARCHAR(20) NOT NULL,
    shelf_num INT NOT NULL,
    level_num INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2.2 도서 마스터 테이블 (Book_Master)
CREATE TABLE Book_Master (
    book_id VARCHAR(50) PRIMARY KEY,
    barcode VARCHAR(50) UNIQUE,
    call_number VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100),
    assigned_loc_id VARCHAR(50) REFERENCES Library_Master(location_id),
    expected_order INT
);

-- 3. 트랜잭션 테이블 생성

-- 3.1 스캔 세션 로그 테이블 (Scan_Session)
CREATE TABLE Scan_Session (
    session_id VARCHAR(50) PRIMARY KEY, -- ✅ 파이썬의 String(50)과 일치시킴
    location_id VARCHAR(50) REFERENCES Library_Master(location_id),
    user_id VARCHAR(50) NOT NULL,
    scan_time TIMESTAMP DEFAULT NOW(),
    image_url VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    lux_level INT,
    overall_status VARCHAR(20) NOT NULL, -- COMPLETED, NEEDS_ACTION
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_image_deleted BOOLEAN DEFAULT FALSE -- 온프레미스 스토리지 정책(7일 후 삭제) 반영 컬럼
);

-- 3.2 AI 인식 상세 결과 테이블 (Scan_Result_Detail)
CREATE TABLE Scan_Result_Detail (
    detection_id VARCHAR(50) PRIMARY KEY, -- ✅ 변경
    session_id VARCHAR(50) REFERENCES Scan_Session(session_id) ON DELETE CASCADE, -- 세션 삭제 시 연쇄 삭제
    matched_book_id VARCHAR(50) REFERENCES Book_Master(book_id), -- 미인식/초과 시 NULL 가능
    
    -- [핵심 변경] AI가 추출한 원본 JSON 데이터 저장 (도서명, 청구기호 등)
    -- 예: {"title": "나미야 잡화점", "call_number": "813.6 히15나"}
    raw_ocr_data JSONB,
    
    confidence DECIMAL(5,2),
    bounding_box JSONB, -- AR 오버레이 및 프론트엔드 확장을 위한 JSONB 타입 적용 {x, y, w, h}
    detected_order INT NOT NULL,
    status VARCHAR(20) NOT NULL -- MATCH, MISPLACED, MISSING, EXTRA, UNKNOWN
);

-- 3.3 수동 수정 이력 테이블 (Manual_Correction)
CREATE TABLE Manual_Correction (
    correction_id VARCHAR(50) PRIMARY KEY DEFAULT VARCHAR(50),
    detection_id VARCHAR(50) REFERENCES Scan_Result_Detail(detection_id),
    user_id VARCHAR(50) NOT NULL,
    corrected_book_id VARCHAR(50) REFERENCES Book_Master(book_id),
    correction_time TIMESTAMP DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL -- TEXT_FIX, BARCODE_MATCH, MERGED, SPLIT
);

-- 4. 성능 최적화를 위한 인덱스(Index) 생성

-- 4.1 특정 서가의 최근 점검 결과를 빠르게 불러오기 위한 복합 인덱스
CREATE INDEX idx_scan_session_loc_time ON Scan_Session (location_id, scan_time DESC);

-- 4.2 대시보드의 '조치 필요(오류)' 리스트 렌더링 속도 최적화용 복합 인덱스
CREATE INDEX idx_scan_result_session_status ON Scan_Result_Detail (session_id, status);

-- 4.3 청구기호 LIKE 및 유사도 검색 속도 극대화를 위한 GIN Trigram 인덱스
CREATE INDEX idx_book_master_call_num_trgm ON Book_Master USING gin (call_number gin_trgm_ops);

-- (선택) 상태값 기준 조회가 빈번할 경우를 대비한 기본 인덱스
CREATE INDEX idx_scan_session_status ON Scan_Session (overall_status);
