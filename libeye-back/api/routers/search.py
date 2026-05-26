from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from database import get_db
from models import BookMaster, ScanResultDetail, ScanSession

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

@router.get("/books")
def search_books(
    q: str = Query(..., description="검색할 도서명 또는 청구기호"), 
    db: Session = Depends(get_db)
):
    """
    도서명 또는 청구기호로 도서를 검색하고,
    원래 지정된 위치(assigned_location)와 
    AI 스캔을 통해 가장 최근에 발견된 위치(last_seen_location)를 함께 반환합니다.
    """
    
    # 1. BookMaster에서 도서명 또는 청구기호로 검색 (부분 일치)
    books = db.query(BookMaster).filter(
        or_(
            BookMaster.title.ilike(f"%{q}%"),
            BookMaster.call_number.ilike(f"%{q}%")
        )
    ).all()

    results = []
    
    for book in books:
        # 2. 해당 도서(book_id)가 마지막으로 스캔된 세션 기록 찾기
        # ScanResultDetail과 ScanSession을 조인하여 가장 최신 세션(created_at 내림차순) 1개를 가져옴
        last_seen_record = db.query(ScanSession.location_id, ScanSession.created_at)\
            .join(ScanResultDetail, ScanResultDetail.session_id == ScanSession.session_id)\
            .filter(ScanResultDetail.matched_book_id == book.book_id)\
            .order_by(desc(ScanSession.created_at))\
            .first()

        results.append({
            "book_id": book.book_id,
            "title": book.title,
            "call_number": book.call_number,
            "assigned_location": book.assigned_loc_id,
            "last_seen_location": last_seen_record.location_id if last_seen_record else None,
            "last_seen_time": last_seen_record.created_at if last_seen_record else None
        })

    return {"results": results}
