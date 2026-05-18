from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import re

# 수정됨: api. 접두사 제거 (컨테이너 내에서는 api 폴더 안의 파일들이 최상위 경로임)
from database import get_db 
# 🚨 수정: ScanImage 모델 임포트 추가
from models import ScanSession, ScanResultDetail, ScanImage, BookMaster

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
        # 🚨 [수정됨] 2. 매칭된 도서(book)가 있다면, 원래 배정된 위치와 순서를 프론트엔드로 전달
        book_info = r.book 
        
        detections.append({
            "detection_id": r.detection_id,
            "source_image_id": r.source_image_id, 
            "detected_order": r.detected_order,
            "bounding_box": r.bounding_box,
            "ocr_title": r.raw_ocr_title,
            "ocr_call_number": r.raw_ocr_call_number,
            "status": r.status,
            "matched_book_id": r.matched_book_id,
            "expected_order": book_info.expected_order if book_info else None,      # 원래 있어야 할 순서
            "assigned_loc_id": book_info.assigned_loc_id if book_info else None,    # 원래 있어야 할 서가 위치 (EXTRA 판별용)
            "crop_image_url": _to_proxy_path(r.crop_image_url),
            "confidence": r.confidence
        })
        
    
    # 🚨 수정: 병합 후 최종 산출된 물리적 순서(detected_order) 기준으로 정렬하여 결과 반환
    results = db.query(ScanResultDetail).filter(ScanResultDetail.session_id == session_id).order_by(ScanResultDetail.detected_order).all()
    
    detections = []
    for r in results:
        detections.append({
            "detection_id": r.detection_id,
            # 🚨 추가됨: 프론트엔드에서 어느 이미지 조각의 결과인지 식별하기 위함
            "source_image_id": r.source_image_id, 
            "detected_order": r.detected_order,
            "bounding_box": r.bounding_box,
            "ocr_title": r.raw_ocr_title,
            "ocr_call_number": r.raw_ocr_call_number,
            "status": r.status,
            "matched_book_id": r.matched_book_id,
            # 상대 경로 반환 → Vite 프록시가 자동으로 백엔드로 전달
            "crop_image_url": _to_proxy_path(r.crop_image_url),
            "confidence": r.confidence
        })
    
    return {
        "session_id": session_id,
        "status": session_info.status,
        "location_id": session_info.location_id, # 🚨 추가됨: 완료 상태일 때 위치 정보 반환
        # 🚨 수정: 기존 "image_url" 단일 키 대신, "images" 배열로 반환
        "images": image_list,
        "expected_books": expected_books, # 🚨 [추가됨] 원본 도서 목록 반환
        "detections": detections
    }
