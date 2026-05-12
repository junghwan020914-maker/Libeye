from sqlalchemy.orm import Session
from sqlalchemy import func

from models import BookMaster
from config import OCR_MATCH_THRESHOLD


def match_book_by_call_number(
    db: Session,
    raw_call_number: str,
    location_id: str | None,
    threshold: float = OCR_MATCH_THRESHOLD,
) -> BookMaster | None:
    """
    OCR로 추출한 청구기호를 BookMaster와 Levenshtein 거리로 비교하여 가장 유사한 책을 반환한다.
    - location_id 있음: 해당 서가 내에서만 검색
    - location_id 없음: 전체 BookMaster에서 검색
    유사도가 threshold(%) 미만이면 None 반환.
    """
    clean = raw_call_number.strip()
    if not clean:
        return None

    query = db.query(
        BookMaster,
        func.levenshtein(BookMaster.call_number, clean).label("distance"),
    )

    if location_id is not None:
        query = query.filter(BookMaster.assigned_loc_id == location_id)

    record = query.order_by("distance").first()

    if not record:
        return None

    matched_book, distance = record
    max_len = max(len(clean), len(matched_book.call_number))
    similarity = ((max_len - distance) / max_len * 100) if max_len > 0 else 0.0

    if similarity >= threshold:
        print(
            f"[매칭 성공] '{clean}' → '{matched_book.call_number}' "
            f"(유사도 {similarity:.1f}%)"
        )
        return matched_book

    print(f"[매칭 실패] '{clean}' (유사도 {similarity:.1f}% < {threshold}%)")
    return None
