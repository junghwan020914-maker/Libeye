import base64
import cv2
import json
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, DATABASE_URL
from storage import s3_client, ensure_buckets_exist, upload_image, download_image
from service.detector import yolo_model, run_detection, crop_spine
from service.ocr import extract_text_with_gemma
from service.matcher import hybrid_book_matching_with_jamo, get_top_candidates
from service.misplacement import detect_misplacements

# 🚨 수정됨: ScanImage 모델 임포트 추가
from models import ScanSession, ScanResultDetail, BookMaster, ScanImage, DailyAnalytics, AnalyticsTotal
import cart_pipeline

# --- 앱 초기화 ---
celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ensure_buckets_exist()


# --- 메인 파이프라인 ---


# 🚨 수정됨: task 이름 및 매개변수 변경 (단일 파일명 대신 세션 ID만 받음)
@celery_app.task(name="process_session_task")
def process_scan_session(session_id: str):
    if yolo_model is None:
        return {"status": "error", "message": "YOLO model not loaded"}

    db = SessionLocal()
    session = None

    # 🚨 추가됨: 모든 이미지의 분석 결과를 하나로 누적할 전역 리스트
    global_results = []

    try:
        session = (
            db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
        )
        if session is None:
            return {"status": "error", "message": f"세션 없음: {session_id}"}

        session.status = "PROCESSING"
        db.commit()

        # 🚨 추가됨: 해당 세션에 속한 이미지들을 물리적 순서(sequence_order)대로 모두 가져옴
        images = (
            db.query(ScanImage)
            .filter(ScanImage.session_id == session_id)
            .order_by(ScanImage.sequence_order)
            .all()
        )

        # 🚨 수정됨: 여러 이미지를 순차적으로 처리하는 루프 추가
        for img_record in images:
            # MinIO URL에서 원본 파일명 추출 (예: session-xxx/img-yyy.jpg)
            original_file_name = img_record.image_url.split("original-bucket/")[-1]

            # 1. MinIO에서 원본 이미지 다운로드
            print(f"[{session_id}] 1. 원본 이미지 다운로드: {original_file_name}")
            img = download_image("original-bucket", original_file_name)
            if img is None:
                print(
                    f"[{session_id}] 이미지 다운로드 실패 (건너뜀): {original_file_name}"
                )
                continue

            # 2. YOLO 탐지
            print(f"[{session_id}] 2. YOLO 탐지 ({img_record.image_id})")
            boxes, masks = run_detection(img)

            local_results = []  # 현재 이미지에서만 탐지된 결과

            if boxes is None or len(boxes) == 0:
                print(f"[{session_id}] 탐지된 책 없음 ({img_record.image_id})")
            else:
                print(f"[{session_id}] {len(boxes)}권 탐지 ({img_record.image_id})")

                for idx, box in enumerate(boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # 3. 마스크 크롭 + MinIO 업로드 (🚨수정됨: 이름 충돌 방지를 위해 image_id 추가)
                    crop_img = crop_spine(img, box, masks, idx)
                    crop_key = f"{session_id}_{img_record.image_id}_crop_{idx}.jpg"
                    crop_url = upload_image("crop-bucket", crop_key, crop_img)

                    # 4. Gemma OCR
                    _, buf = cv2.imencode(".jpg", crop_img)
                    b64 = base64.b64encode(buf).decode("utf-8")
                    print(f"[{session_id}] OCR 요청 중 (crop {idx})")
                    ocr_result = extract_text_with_gemma(b64)

                    # 5. DB 하이브리드 퍼지 매칭 (기존 로직 그대로 유지)
                    raw_call_number = ocr_result.get("call_number", "")
                    raw_title = ocr_result.get("title", "")

                    matched = None
                    if raw_call_number.strip():
                        print(
                            f"[{session_id}] 1차 전역 DB 검색 (청구기호: {raw_call_number})"
                        )
                        top_candidates = get_top_candidates(
                            db, raw_call_number, limit=5
                        )

                        print(
                            f"[{session_id}] 2차 하이브리드 정밀 매칭 (후보 {len(top_candidates)}건)"
                        )
                        matched = hybrid_book_matching_with_jamo(
                            raw_call_number, raw_title, top_candidates
                        )
                    else:
                        print(f"[{session_id}] 청구기호 OCR 실패로 매칭 생략")

                    polygon = None
                    if masks is not None and len(masks.xy) > idx:
                        polygon = masks.xy[idx].tolist()

                    local_results.append(
                        {
                            "source_image_id": img_record.image_id,  # 🚨 추가됨: 출처 이미지 기록
                            "bounding_box": {
                                "polygon": polygon,
                            },
                            "raw_ocr_data": ocr_result,
                            "matched_book_id": matched.book_id if matched else None,
                            "matched_call_number": matched.call_number if matched else None,
                            "matched_title": matched.title if matched else None,
                            "assigned_loc_id": matched.assigned_loc_id
                            if matched
                            else None,
                            "expected_order": matched.expected_order
                            if matched
                            else None,
                            "confidence": int(box.conf[0] * 100),
                            "crop_url": crop_url,
                        }
                    )

            # 현재 이미지 내에서 물리적 순서(x 좌표)대로 먼저 정렬
            local_results.sort(key=lambda r: r["bounding_box"]["polygon"][0][0] if r["bounding_box"]["polygon"] else 0)

            # 🚨 [핵심 알고리즘] 중복 제거(Deduplication) 및 병합 로직
            if global_results and local_results:
                # N번째 이미지의 우측 끝 3권과 N+1번째 이미지의 좌측 끝 3권을 교차 비교
                overlap_window = 3
                last_globals = global_results[-overlap_window:]
                first_locals = local_results[:overlap_window]

                duplicate_local_indices = set()

                for l_idx, l_book in enumerate(first_locals):
                    for g_idx_offset, g_book in enumerate(last_globals):
                        g_idx = len(global_results) - overlap_window + g_idx_offset
                        if g_idx < 0:
                            continue

                        is_match = False

                        # 기준 1: 매칭된 정답 도서 ID가 동일한 경우
                        if g_book["matched_book_id"] and l_book["matched_book_id"]:
                            if g_book["matched_book_id"] == l_book["matched_book_id"]:
                                is_match = True
                        # 기준 2: 정답은 못 찾았지만 OCR 추출 청구기호 텍스트가 완전히 일치하는 경우
                        elif g_book["raw_ocr_data"].get("call_number") and l_book[
                            "raw_ocr_data"
                        ].get("call_number"):
                            if (
                                g_book["raw_ocr_data"]["call_number"]
                                == l_book["raw_ocr_data"]["call_number"]
                            ):
                                is_match = True

                        if is_match:
                            # 동일한 책으로 판별됨: 신뢰도(Confidence)가 더 높은 쪽 정보로 갱신
                            if l_book["confidence"] > g_book["confidence"]:
                                global_results[g_idx] = l_book

                            # 현재 이미지의 해당 도서는 전역 리스트에 중복 추가하지 않도록 마킹
                            duplicate_local_indices.add(l_idx)
                            break  # 매칭 찾았으면 다음 로컬 도서로 넘어감

                # 중복 마킹되지 않은 새로운 도서들만 전역 리스트의 뒤에 이어 붙임
                for l_idx, l_book in enumerate(local_results):
                    if l_idx not in duplicate_local_indices:
                        global_results.append(l_book)
            else:
                # 첫 번째 이미지이거나, 전역 리스트가 비어있으면 그대로 병합
                global_results.extend(local_results)

        # 6. 병합된 전체 리스트를 통해 오배열 판별
        # (이미 sequence_order 순서대로 병합되면서 물리적 순서가 완성된 상태)

        # 6. 병합된 전체 리스트를 통해 오배열 판별
        # location_id가 없으면 detect_misplacements 내부에서 다수결로 추론
        print(f"[{session_id}] 6. 오배열 판별 (총 {len(global_results)}권 병합됨)")
        final_results, resolved_loc, inferred_loc = detect_misplacements(
            global_results, session.location_id if session else None
        )

        # location_id가 없었던 경우 추론된 값을 세션에 저장
        if session and not session.location_id and resolved_loc:
            session.location_id = resolved_loc
            print(f"[{session_id}] location_id 추론 완료: {resolved_loc}")

        # 선택한 서가와 실제 책들의 서가가 다른 경우 기록
        if session and inferred_loc:
            session.inferred_location_id = inferred_loc
            print(f"[{session_id}] 서가 불일치 감지: 선택={session.location_id}, 실제={inferred_loc}")

        # 7. DB 저장
        print(f"[{session_id}] 7. 결과 저장")
        for idx, result in enumerate(final_results):
            ocr = result.get("raw_ocr_data", {})

            # 🚨 [수정됨] 논리형(bool) 등이 들어올 수 있으므로 str()로 확실히 변환 후 슬라이싱
            raw_title = ocr.get("title", "")
            if raw_title:
                raw_title = str(raw_title)[:255]

            raw_call_number = ocr.get("call_number", "")
            if raw_call_number:
                raw_call_number = str(raw_call_number)[:100]

            db.add(
                ScanResultDetail(
                    detection_id=f"{session_id}-det-{idx}",
                    session_id=session_id,
                    source_image_id=result.get("source_image_id"),
                    # 🚨 [이전 오류 수정] 파이썬 딕셔너리를 JSON 문자열로 변환 (파일 상단에 import json 필요)
                    bounding_box=json.dumps(result.get("bounding_box", {})),
                    raw_ocr_title=raw_title,
                    raw_ocr_call_number=raw_call_number,
                    matched_book_id=result["matched_book_id"],
                    detected_order=idx + 1,
                    status=result["status"],
                    confidence=result["confidence"],
                    crop_image_url=result.get("crop_url"),
                )
            )

        # 8. ScanSession 집계 컬럼 업데이트
        # MISSING은 탐지된 책이 아니라 DB에서 추론된 누락이므로 total_books에서 제외
        total_books = len(final_results)
        misplaced_count = sum(1 for r in final_results if r["status"] == "MISPLACED")
        unknown_count = sum(1 for r in final_results if r["status"] == "UNKNOWN")

        if session:
            session.status = "COMPLETED"
            session.total_books = total_books
            session.misplaced_count = misplaced_count
            session.unknown_count = unknown_count

        # 9. DailyAnalytics upsert — 날짜별 집계 캐시 갱신 (주간 차트용)
        from datetime import date as date_type
        today = date_type.today()
        daily = db.query(DailyAnalytics).filter(DailyAnalytics.date == today).first()
        if daily is None:
            daily = DailyAnalytics(date=today)
            db.add(daily)
        daily.total_scans = (daily.total_scans or 0) + total_books
        daily.misplaced_count = (daily.misplaced_count or 0) + misplaced_count
        daily.unknown_count = (daily.unknown_count or 0) + unknown_count
        daily.session_count = (daily.session_count or 0) + 1

        # 10. AnalyticsTotal upsert — 전체 누적 집계 갱신 (오류비율/AI성공률용)
        total_row = db.query(AnalyticsTotal).filter(AnalyticsTotal.id == 1).first()
        if total_row is None:
            total_row = AnalyticsTotal(id=1)
            db.add(total_row)
        total_row.total_scans = (total_row.total_scans or 0) + total_books
        total_row.misplaced_count = (total_row.misplaced_count or 0) + misplaced_count
        total_row.unknown_count = (total_row.unknown_count or 0) + unknown_count
        total_row.session_count = (total_row.session_count or 0) + 1

        db.commit()

        print(f"[{session_id}] 파이프라인 완료")
        return {"status": "success", "session_id": session_id}

    except Exception as e:
        # 🚨 [수정 2] 에러 발생 시 진행 중이던 트랜잭션 롤백
        db.rollback()
        print(f"[{session_id}] 오류 발생: {e}")

        # 🚨 [수정 3] 상태를 확실하게 FAILED로 저장
        if session:
            try:
                session.status = "FAILED"
                db.add(session)
                db.commit()
                print(f"[{session_id}] 세션 상태 FAILED 업데이트 완료")
            except Exception as inner_e:
                db.rollback()
                print(f"[{session_id}] 상태 업데이트마저 실패: {inner_e}")

        # 🚨 [수정 4] Celery가 이 작업을 '실패'로 인식하도록 에러를 뱉어냄
        raise e

    finally:
        db.close()

