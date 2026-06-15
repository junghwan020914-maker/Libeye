import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

# 💡 사용자님의 docker-compose.yml 실제 환경 변수와 100% 일치하도록 매핑했습니다!
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "libeye_db")         # 수정: libeye_db
DB_USER = os.getenv("DB_USER", "libeye_admin")      # 수정: libeye_admin
DB_PASSWORD = os.getenv("DB_PASSWORD", "libeye_admin_pwd")  # 수정: libeye_admin_pwd
DB_PORT = os.getenv("DB_PORT", "5432")

OUTPUT_CSV_PATH = "./final_evaluation_results.csv"

def extract_metrics_from_database():
    print(f"🔌 PostgreSQL 데이터베이스({DB_HOST}:{DB_PORT}/{DB_NAME})에 연결을 시도합니다...")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST, 
            database=DB_NAME, 
            user=DB_USER, 
            password=DB_PASSWORD, 
            port=DB_PORT,
            connect_timeout=5 # 💡 연결 실패 시 무한 대기하지 않고 5초 뒤 타임아웃 에러를 내도록 안전장치 추가
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("💡 [팁] 도커 컨테이너가 정상적으로 켜져 있는지 'docker compose ps'로 확인해 주세요.")
        return

    # 성능 지표 및 로그 매핑 통합 SQL 쿼리
    query = """
        SELECT 
            ss.session_id,
            ss.location_id,
            ss.overall_status AS final_status,
            split_part(ss.image_path, '/', cardinality(string_to_array(ss.image_path, '/'))) AS filename,
            (SELECT COUNT(*) FROM Scan_Result_Detail WHERE session_id = ss.session_id) AS total_detected,
            (SELECT COUNT(*) FROM Scan_Result_Detail WHERE session_id = ss.session_id AND status IN ('MISPLACED', 'MISSING')) AS error_count,
            COALESCE((
                SELECT AVG((call_number_score + title_score) / 2.0) 
                FROM Scan_Result_Detail 
                WHERE session_id = ss.session_id AND call_number_score IS NOT NULL AND title_score IS NOT NULL
            ), 0.0) AS Final_match_percent,
            ss.yolo_duration AS YOLO_time,
            ss.vlm_duration AS OCR_time,
            ss.matching_duration AS In_Out_time
        FROM Scan_Session ss
        ORDER BY ss.scan_time ASC;
    """

    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        print(f"❌ 쿼리 실행 중 오류 발생: {e}")
        cur.close()
        conn.close()
        return

    if not rows:
        print("⚠ 데이터베이스에 추출할 수 있는 점검 세션 로그 데이터가 존재하지 않습니다.")
        cur.close()
        conn.close()
        return

    csv_headers = [
        "filename", "location_id", "session_id", "final_status", 
        "total_detected", "error_count", "Final_match_percent(%)", 
        "YOLO_time(s)", "OCR_time(s)", "In_Out_time(s)", "Final_time_sec(s)"
    ]

    total_sessions = len(rows)
    sum_detected = 0
    sum_errors = 0
    sum_match_percent = 0.0
    sum_yolo = 0.0
    sum_ocr = 0.0
    sum_in_out = 0.0
    sum_final = 0.0

    print(f"📊 총 {total_sessions}개의 점검 로그 레코드를 파싱하여 CSV 작성을 시작합니다.")

    with open(OUTPUT_CSV_PATH, mode='w', newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_headers)

        for row in rows:
            yolo_t = float(row['yolo_time']) if row['yolo_time'] else 0.0
            ocr_t = float(row['ocr_time']) if row['ocr_time'] else 0.0
            in_out_t = float(row['in_out_time']) if row['in_out_time'] else 0.0
            final_t = yolo_t + ocr_t + in_out_t

            sum_detected += row['total_detected']
            sum_errors += row['error_count']
            sum_match_percent += float(row['final_match_percent'])
            sum_yolo += yolo_t
            sum_ocr += ocr_t
            sum_in_out += in_out_t
            sum_final += final_t

            writer.writerow([
                row['filename'],
                row['location_id'],
                row['session_id'],
                row['final_status'],
                row['total_detected'],
                row['error_count'],
                f"{row['final_match_percent']:.2f}",
                f"{yolo_t:.3f}",
                f"{ocr_t:.3f}",
                f"{in_out_t:.3f}",
                f"{final_t:.3f}"
            ])

        avg_row = [
            "AVERAGE (평균값)",
            "-",
            "-",
            "-",
            f"{sum_detected / total_sessions:.1f}",
            f"{sum_errors / total_sessions:.1f}",
            f"{sum_match_percent / total_sessions:.2f}",
            f"{sum_yolo / total_sessions:.3f}",
            f"{sum_ocr / total_sessions:.3f}",
            f"{sum_in_out / total_sessions:.3f}",
            f"{sum_final / total_sessions:.3f}"
        ]
        writer.writerow([])
        writer.writerow(avg_row)

    print(f"✅ [추출 완료] 성능 평가 파일 생성 성공!")
    print(f"💾 결과 저장 경로: {os.path.abspath(OUTPUT_CSV_PATH)}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    extract_metrics_from_database()