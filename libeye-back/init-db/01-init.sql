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
    session_id VARCHAR(50) PRIMARY KEY,
    location_id VARCHAR(50) REFERENCES Library_Master(location_id),
    scan_time TIMESTAMP DEFAULT NOW(),
    -- 🚨 수정됨: image_url 및 is_image_deleted 컬럼 삭제
    status VARCHAR(20) DEFAULT 'PENDING',
    lux_level INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- 🚨 [추가됨] 수정 발생 시 시간을 추적하기 위한 컬럼
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- 세션 완료 시 파이프라인이 채워주는 집계 컬럼
    total_books INT DEFAULT 0,               -- YOLO가 탐지한 총 책 권수
    misplaced_count INT DEFAULT 0,           -- 오배열 책 수 (MISPLACED)
    unknown_count INT DEFAULT 0,             -- 인식 실패 총합 (ocr_failed_count + match_failed_count)
    ocr_failed_count INT DEFAULT 0,          -- OCR 자체 실패 수 (텍스트 추출 불가, OCR_FAILED)
    match_failed_count INT DEFAULT 0,        -- OCR은 됐으나 DB 매칭 실패 수 (MATCH_FAILED)
    inferred_location_id VARCHAR(50),        -- 책 다수결로 추론된 실제 서가 ID (선택한 서가와 다를 때만 저장)
    elapsed_sec FLOAT                        -- 파이프라인 총 소요시간 (초)
);

-- 🚨 3.2 [신규 추가] 스캔 이미지 조각 테이블 (Scan_Image)
CREATE TABLE Scan_Image (
    image_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES Scan_Session(session_id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    sequence_order INT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 3.3 AI 인식 상세 결과 테이블 (Scan_Result_Detail)
CREATE TABLE Scan_Result_Detail (
    detection_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES Scan_Session(session_id) ON DELETE CASCADE,
    -- 🚨 수정됨: source_image_id 추가 및 외래키 설정
    source_image_id VARCHAR(50) REFERENCES Scan_Image(image_id) ON DELETE SET NULL,
    matched_book_id VARCHAR(50) REFERENCES Book_Master(book_id),

    raw_ocr_title VARCHAR(255),
    raw_ocr_call_number VARCHAR(100),
    crop_image_url VARCHAR(255),

    confidence DECIMAL(5,2),
    -- 🌟 [추가됨] matcher.py가 산출한 최고 매칭 점수 (0~100, 매칭 실패 시에도 최고 점수 저장)
    highest_score DECIMAL(5,2) DEFAULT 0,
    bounding_box JSONB,
    detected_order INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    -- 🚨 [추가됨] 프론트엔드에서 오배열 확인(조치) 완료 여부
    is_verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(20) DEFAULT NULL
);

-- 3.4 수동 수정 이력 테이블 (Manual_Correction)
CREATE TABLE Manual_Correction (
    correction_id VARCHAR(50) PRIMARY KEY,
    detection_id VARCHAR(50) REFERENCES Scan_Result_Detail(detection_id),
    user_id VARCHAR(50) NOT NULL,
    corrected_book_id VARCHAR(50) REFERENCES Book_Master(book_id),
    correction_time TIMESTAMP DEFAULT NOW(),
    action_type VARCHAR(50) NOT NULL -- TEXT_FIX, BARCODE_MATCH, MERGED, SPLIT
);

-- 4. 분석 집계 테이블 생성

-- 4.1 날짜별 집계 캐시 테이블 (Daily_Analytics) — 주간 차트용
CREATE TABLE Daily_Analytics (
    date DATE PRIMARY KEY,
    total_scans INT DEFAULT 0,               -- 해당 날 총 인식 책 권수
    misplaced_count INT DEFAULT 0,           -- 오배열 수 (MISPLACED)
    unknown_count INT DEFAULT 0,             -- 인식 실패 총합 (ocr_failed_count + match_failed_count)
    ocr_failed_count INT DEFAULT 0,          -- OCR 자체 실패 수 (OCR_FAILED)
    match_failed_count INT DEFAULT 0,        -- DB 매칭 실패 수 (MATCH_FAILED)
    session_count INT DEFAULT 0,             -- 완료된 세션 수
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4.2 전체 누적 집계 테이블 (Analytics_Total) — 오류비율/AI성공률용, 항상 id=1 단일 행
CREATE TABLE Analytics_Total (
    id INT PRIMARY KEY DEFAULT 1,
    total_scans INT DEFAULT 0,               -- 전체 누적 인식 책 권수
    misplaced_count INT DEFAULT 0,           -- 전체 누적 오배열 수 (MISPLACED)
    unknown_count INT DEFAULT 0,             -- 전체 누적 인식 실패 총합 (ocr_failed_count + match_failed_count)
    ocr_failed_count INT DEFAULT 0,          -- 전체 누적 OCR 자체 실패 수 (OCR_FAILED)
    match_failed_count INT DEFAULT 0,        -- 전체 누적 DB 매칭 실패 수 (MATCH_FAILED)
    session_count INT DEFAULT 0,             -- 전체 누적 세션 수
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT analytics_total_single_row CHECK (id = 1) -- 단일 행 강제
);

-- 초기 행 삽입 (파이프라인이 upsert 기준으로 사용)
INSERT INTO Analytics_Total (id) VALUES (1);

-- 5. 성능 최적화를 위한 인덱스(Index) 생성

-- 5.1 특정 서가의 최근 점검 결과를 빠르게 불러오기 위한 복합 인덱스
CREATE INDEX idx_scan_session_loc_time ON Scan_Session (location_id, scan_time DESC);

-- 5.2 대시보드의 '조치 필요(오류)' 리스트 렌더링 속도 최적화용 복합 인덱스
CREATE INDEX idx_scan_result_session_status ON Scan_Result_Detail (session_id, status);

-- 5.3 청구기호 LIKE 및 유사도 검색 속도 극대화를 위한 GIN Trigram 인덱스
CREATE INDEX idx_book_master_call_num_trgm ON Book_Master USING gin (call_number gin_trgm_ops);

-- (선택) 상태값 기준 조회가 빈번할 경우를 대비한 기본 인덱스
CREATE INDEX idx_scan_session_status ON Scan_Session (status);
