from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel # 🚨 추가
from sqlalchemy.orm import Session
from sqlalchemy import func # 🚨 추가
import re
from app.dependencies import get_db
# 🚨 수정: ScanImage 모델 임포트 추가
from app.models import ScanSession, ScanResultDetail, ScanImage, BookMaster

router = APIRouter(prefix="/api/v1/sessions", tags=["Results"])

# MinIO 내부 URL 패턴: http://minio:9000/{bucket}/{key}
_MINIO_URL_PATTERN = re.compile(r"https?://[^/]+/([^/]+)/(.+)")

def _to_proxy_path(minio_url: str) -> str | None:
    """
    MinIO 내부 URL (http://minio:9000/bucket/key)을
    프론트엔드 상대 경로 (/api/v1/image-proxy/bucket/key)로 변환합니다.
    
    절대 URL이 아닌 상대 경로를 반환하므로:
    - 브라우저가 현재 접속한 프론트엔드 서버(Vite)를 기준으로 요청
    - Vite 프록시가 /api/* → 백엔드로 자동 전달
    - HTTP/HTTPS 불일치(Mixed Content) 문제 없음
    - 방화벽 포트 막힘 문제 없음
    """
    if not minio_url:
        return None
    m = _MINIO_URL_PATTERN.match(minio_url)
    if not m:
        return minio_url
    bucket, key = m.group(1), m.group(2)
    return f"/api/v1/image-proxy/{bucket}/{key}"

@router.get("/{session_id}/results")
async def get_scan_results(session_id: str, db: Session = Depends(get_db)):
    """
    대시보드 또는 AR 클라이언트에서 분석 완료 결과를 조회하는 API.
    이미지 URL은 상대 경로(/api/v1/image-proxy/...)로 반환되며,
    Vite 개발 서버 프록시가 백엔드로 자동 전달합니다.
    """
    session_info = db.query(ScanSession).filter(ScanSession.session_id == session_id).first()
    
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_info.status != "COMPLETED":
        return {
            "session_id": session_id,
            "status": session_info.status,
            "location_id": session_info.location_id, # 🚨 추가됨: 로딩 중일 때도 위치를 표시하기 위함
            "message": "AI analysis is not completed yet."
        }
        
    # 🚨 수정: 해당 세션의 여러 이미지 조각들을 sequence_order 순으로 가져오기
    images = db.query(ScanImage).filter(ScanImage.session_id == session_id).order_by(ScanImage.sequence_order).all()
    image_list = [{
        "image_id": img.image_id,
        "image_url": _to_proxy_path(img.image_url),
        "sequence_order": img.sequence_order
    } for img in images]
        
    # 🚨 [추가됨] 1. 해당 서가(location_id)에 원래 배정된 '전체 도서 목록' 조회 (순서대로)
    expected_books_query = db.query(BookMaster).filter(
        BookMaster.assigned_loc_id == session_info.location_id
    ).order_by(BookMaster.expected_order).all()
    
    expected_books = [{
        "book_id": b.book_id,
        "title": b.title,
        "call_number": b.call_number,
        "expected_order": b.expected_order
    } for b in expected_books_query]
        
    results = db.query(ScanResultDetail).filter(ScanResultDetail.session_id == session_id).order_by(ScanResultDetail.detected_order).all()

    detections = []
    for r in results:
        book_info = r.book
        detections.append({
            "detection_id": r.detection_id,
            "source_image_id": r.source_image_id,
            "detected_order": r.detected_order,
            "bounding_box": r.bounding_box,
            "ocr_title": r.raw_ocr_title,
            "ocr_call_number": r.raw_ocr_call_number,
            "status": r.status,
            "is_verified": r.is_verified, # 🚨 [추가됨] 조치 완료 여부 전달
            "matched_book_id": r.matched_book_id,
            "matched_call_number": book_info.call_number if book_info else None,
            "matched_title": book_info.title if book_info else None,
            "expected_order": book_info.expected_order if book_info else None,
            "assigned_loc_id": book_info.assigned_loc_id if book_info else None,
            "crop_image_url": _to_proxy_path(r.crop_image_url),
            "confidence": r.confidence,
            # 🌟 [추가됨] matcher.py 최고 매칭 점수 (인식 실패/완료 도서 모두 점수 확인용)
            "highest_score": r.highest_score
        })

    location_warning = (
        {
            "selected_location_id": session_info.location_id,
            "actual_location_id": session_info.inferred_location_id,
        }
        if session_info.inferred_location_id
        else None
    )

    return {
        "session_id": session_id,
        "status": session_info.status,
        "location_id": session_info.location_id,
        "location_warning": location_warning,
        # 🚨 수정: 기존 "image_url" 단일 키 대신, "images" 배열로 반환
        "images": image_list,
        "expected_books": expected_books, # 🚨 [추가됨] 원본 도서 목록 반환
        "detections": detections
    }

# 🚨 [신규 추가] 수동 강제 매칭 API 및 재계산 로직
class MatchRequest(BaseModel):
    book_id: str

@router.put("/{session_id}/detections/{detection_id}/match")
def force_match_detection(session_id: str, detection_id: str, req: MatchRequest, db: Session = Depends(get_db)):
    """수동 교정 후 도서를 강제 매칭하고, 해당 서가의 전체 오배열 상태를 LIS 기반으로 재계산합니다."""
    
    det = db.query(ScanResultDetail).filter_by(session_id=session_id, detection_id=detection_id).first()
    if not det: raise HTTPException(status_code=404, detail="Detection not found")
    
    book = db.query(BookMaster).filter_by(book_id=req.book_id).first()
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    
    # 1. DB 매칭 정보 강제 덮어쓰기
    det.matched_book_id = book.book_id
    
    # 2. 오배열 상태(Misplacement) 재계산 (최장 증가 부분 수열 알고리즘 활용)
    session = db.query(ScanSession).filter_by(session_id=session_id).first()
    session.updated_at = func.now() # 업데이트 시간 트리거
    
    all_dets = db.query(ScanResultDetail).filter_by(session_id=session_id).order_by(ScanResultDetail.detected_order).all()
    
    # 🚨 [신규 추가] 세션 내에서 중복 할당된 book_id 추출
    matched_ids = [d.matched_book_id for d in all_dets if d.matched_book_id]
    duplicate_book_ids = {bid for bid in matched_ids if matched_ids.count(bid) > 1}

    valid_seq = []
    for d in all_dets:
        if d.matched_book_id:
            # 🚨 [신규 추가] 동일한 책에 중복 매칭된 경우 'DUPLICATE' 상태 부여 후 LIS 대상에서 제외
            if d.matched_book_id in duplicate_book_ids:
                d.status = 'DUPLICATE'
                continue
                
            b = db.query(BookMaster).filter_by(book_id=d.matched_book_id).first()
            if b.assigned_loc_id == session.location_id:
                valid_seq.append((d, b.expected_order))
            else:
                d.status = 'EXTRA'
        else:
            d.status = 'UNKNOWN'
            
    if valid_seq:
        import bisect
        tails = []
        parent = {}
        tail_indices = []
        
        for i, (d, exp_order) in enumerate(valid_seq):
            idx = bisect.bisect_left(tails, exp_order)
            if idx == len(tails):
                tails.append(exp_order)
                tail_indices.append(i)
            else:
                tails[idx] = exp_order
                tail_indices[idx] = i
            
            parent[i] = tail_indices[idx - 1] if idx > 0 else -1
            
        lis_indices = set()
        curr = tail_indices[-1] if tail_indices else -1
        while curr != -1:
            lis_indices.add(curr)
            curr = parent[curr]
            
        for i, (d, exp_order) in enumerate(valid_seq):
            d.status = 'MATCH' if i in lis_indices else 'MISPLACED'
                
    db.commit()
    return {"message": "Matched successfully and recalculated status"}

# 1. 기존 개별 조치 완료 API (MANUAL 기록)
@router.put("/{session_id}/detections/{detection_id}/verify")
def verify_misplacement(session_id: str, detection_id: str, db: Session = Depends(get_db)):
    det = db.query(ScanResultDetail).filter_by(session_id=session_id, detection_id=detection_id).first()
    if not det: raise HTTPException(status_code=404, detail="Detection not found")
    
    det.is_verified = True
    det.verification_method = 'MANUAL' # 🌟 개별 확인 기록
    db.commit()
    return {"message": "Verification completed"}

# libeye-back/api/routers/results.py 파일 하단에 추가

@router.delete("/{session_id}/detections/{detection_id}")
def delete_false_detection(session_id: str, detection_id: str, db: Session = Depends(get_db)):
    """YOLO가 잘못 탐지한 이미지(책이 아닌 객체)를 삭제하고 서가 배열 상태를 재계산합니다."""
    
    det = db.query(ScanResultDetail).filter_by(session_id=session_id, detection_id=detection_id).first()
    if not det: 
        raise HTTPException(status_code=404, detail="Detection not found")
    
    # 1. 탐지 결과 DB에서 완전히 삭제
    db.delete(det)
    
    # 2. 오배열 상태 재계산을 위해 세션 업데이트 트리거
    session = db.query(ScanSession).filter_by(session_id=session_id).first()
    session.updated_at = func.now()
    
    # 3. 남은 도서들을 다시 불러와서 오배열(LIS) 재계산
    remaining_dets = db.query(ScanResultDetail).filter_by(session_id=session_id).order_by(ScanResultDetail.detected_order).all()
    
    valid_seq = []
    for d in remaining_dets:
        if d.matched_book_id:
            b = db.query(BookMaster).filter_by(book_id=d.matched_book_id).first()
            if b and b.assigned_loc_id == session.location_id:
                valid_seq.append((d, b.expected_order))
            else:
                d.status = 'EXTRA'
        else:
            d.status = 'UNKNOWN'
            
    if valid_seq:
        import bisect
        tails = []
        parent = {}
        tail_indices = []
        
        for i, (d, exp_order) in enumerate(valid_seq):
            idx = bisect.bisect_left(tails, exp_order)
            if idx == len(tails):
                tails.append(exp_order)
                tail_indices.append(i)
            else:
                tails[idx] = exp_order
                tail_indices[idx] = i
            
            parent[i] = tail_indices[idx - 1] if idx > 0 else -1
            
        lis_indices = set()
        curr = tail_indices[-1] if tail_indices else -1
        while curr != -1:
            lis_indices.add(curr)
            curr = parent[curr]
            
        for i, (d, exp_order) in enumerate(valid_seq):
            d.status = 'MATCH' if i in lis_indices else 'MISPLACED'
                
    db.commit()
    return {"message": "Detection deleted and status recalculated"}

# 🚨 [신규 추가] 세션 내 모든 오배열 일괄 조치 완료 반영 API
# 2. 일괄 조치 완료 API (BATCH_OVERWRITE 기록)
@router.put("/{session_id}/verify-all")
def verify_all_actions(session_id: str, db: Session = Depends(get_db)):
    unverified_dets = db.query(ScanResultDetail).filter(
        ScanResultDetail.session_id == session_id, 
        ScanResultDetail.status.in_(['MISPLACED', 'UNKNOWN', 'EXTRA']),
        ScanResultDetail.is_verified == False
    ).all()
    
    for det in unverified_dets:
        det.is_verified = True
        det.verification_method = 'BATCH_OVERWRITE' # 🌟 강제 일괄 덮어쓰기 기록
        
    db.commit()
    return {"message": "All pending actions overwritten successfully", "updated_count": len(unverified_dets)}