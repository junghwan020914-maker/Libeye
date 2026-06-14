from typing import Iterable, Optional, List, Set, Tuple

from thefuzz import fuzz
from jamo import h2j, j2hcj
from sqlalchemy.orm import Session

from models import BookMaster

WEIGHT_CALL_NUM = 0.5
WEIGHT_TITLE = 0.5
MATCH_THRESHOLD = 80.0

def get_top_candidates_by_call_number(db: Session, ocr_call_number: str, limit: int = 5) -> List[BookMaster]:
    """
    [1-A단계 검색] PostgreSQL pg_trgm 확장의 <-> 연산자를 사용하여
    전체 DB에서 청구기호가 가장 유사한 Top N개의 도서를 추출합니다.
    """
    # ✨ 어떤 타입(float, bool 등)이 들어와도 안전하게 문자열로 변환 후 strip 처리
    clean_call = "" if isinstance(ocr_call_number, bool) else str(ocr_call_number or "").strip()
    
    # NaN 결측치가 문자열 "nan"으로 변환된 경우도 빈 값으로 처리하여 검색에서 제외합니다.
    if not clean_call or clean_call.lower() == "nan":
        return []

    return (
        db.query(BookMaster)
        .order_by(BookMaster.call_number.op('<->')(clean_call))
        .limit(limit)
        .all()
    )


def get_top_candidates_by_title(db: Session, ocr_title: str, limit: int = 5) -> List[BookMaster]:
    """
    [1-B단계 검색] PostgreSQL pg_trgm 확장의 <-> 연산자를 사용하여
    전체 DB에서 도서명이 가장 유사한 Top N개의 도서를 추출합니다.
    """
    # ✨ 어떤 타입(float, bool 등)이 들어와도 안전하게 문자열로 변환 후 strip 처리
    clean_title = "" if isinstance(ocr_title, bool) else str(ocr_title or "").strip()
    
    # NaN 결측치가 문자열 "nan"으로 변환된 경우도 빈 값으로 처리하여 검색에서 제외합니다.
    if not clean_title or clean_title.lower() == "nan":
        return []

    return (
        db.query(BookMaster)
        .order_by(BookMaster.title.op('<->')(clean_title))
        .limit(limit)
        .all()
    )


def decompose_korean(text: str) -> str:
    """한글 텍스트를 초성·중성·종성(자소) 단위로 분해."""
    if not text or isinstance(text, bool):
        return ""
    
    text_str = str(text)
    try:
        return j2hcj(h2j(text_str))
    except Exception:
        return text_str


def hybrid_book_matching_with_jamo(
    ocr_call_number: str,
    ocr_title: str,
    db_candidates: Iterable[BookMaster],
) -> Tuple[Optional[BookMaster], float]:
    """
    [2단계 검색] 청구기호(일반 퍼지)와 도서명(자소 분리 퍼지)을 가중합한 하이브리드 매칭.

    반환값: (best_match, highest_score)
      - 매칭 성공 시: (확정 도서, 최고 점수)
      - 매칭 실패 시: (None, 최고 점수)  ← 임계값 미달이어도 가장 높았던 점수를 함께 반환
    """
    # 청구기호와 제목 둘 다 비어있으면 매칭 불가
    clean_call = "" if isinstance(ocr_call_number, bool) else str(ocr_call_number or "").strip()
    safe_title = "" if isinstance(ocr_title, bool) else str(ocr_title or "").strip()

    if not clean_call and not safe_title:
        return None, 0.0

    ocr_title_jamo = decompose_korean(safe_title)

    best_match: Optional[BookMaster] = None
    highest_score = 0.0

    for book in db_candidates:
        # 1. 청구기호 점수 계산 (OCR 결과가 있을 때만 계산, 없으면 0점)
        if clean_call:
            call_num_score = max(
                fuzz.ratio(clean_call, book.call_number),
                fuzz.partial_ratio(clean_call, book.call_number),
                fuzz.token_sort_ratio(clean_call, book.call_number),
            )
        else:
            call_num_score = 0.0
        
        # 2. 제목 점수 계산 (OCR 결과가 있을 때만 계산, 없으면 0점)
        if safe_title:
            db_title_jamo = decompose_korean(safe_title)
            
            # 🛠️ [방어 로직 추가] OCR 제목이 지나치게 짧은 경우 오작동 방지
            clean_title_len = len(safe_title.strip())
            
            if clean_title_len > 5:
                # 일반적인 상황: 부분 일치(partial_ratio) 허용
                title_score = max(
                    fuzz.token_sort_ratio(ocr_title_jamo, db_title_jamo),
                    fuzz.partial_ratio(ocr_title_jamo, db_title_jamo)
                )
            else:
                # 🚨 5글자 이하(노이즈 혹은 단일 글자)일 때는 partial_ratio를 제외!
                # 전체적인 자소 구성 비율만 따지도록 하여 '느낌의 0도' 같은 긴 제목이 만점 받는 것을 방지합니다.
                title_score = fuzz.token_sort_ratio(ocr_title_jamo, db_title_jamo)
        else:
            title_score = 0.0
        
        
        # 3. 최종 가중합 산출
        final_score = call_num_score * WEIGHT_CALL_NUM + title_score * WEIGHT_TITLE

        # ✨ [개선] 청구기호 점수가 100점(완벽 일치)인 경우의 구제 로직
        if call_num_score == 100:
            # 최소 85점을 보장하고, 제목 점수의 15%를 더해 85.0 ~ 100.0 점 사이로 보정합니다.
            # 이를 통해 제목이 0점이어도 85점으로 MATCH_THRESHOLD(80.0)를 통과합니다.
            # 만약 같은 청구기호의 다른 책이 있다면 제목이 더 유사한 책이 최종 선택됩니다.
            boosted_score = 85.0 + (title_score * 0.15)
            final_score = max(final_score, boosted_score)

        print(
            f"[{book.title}] 청구점수:{call_num_score}, "
            f"제목점수(자소):{title_score} -> 최종:{final_score:.1f}"
        )

        if final_score > highest_score:
            highest_score = final_score
            best_match = book
      

    if best_match is not None and highest_score >= MATCH_THRESHOLD:
        print(
            f"[매칭 성공] '{clean_call}' / '{safe_title}' → "
            f"'{best_match.call_number}' / '{best_match.title}' "
            f"(점수 {highest_score:.1f})"
        )
        return best_match, highest_score

    print(f"[매칭 실패] '{clean_call}' / '{safe_title}' (최고 점수 {highest_score:.1f} < {MATCH_THRESHOLD})")
    return None, highest_score


def match_book_pipeline(db: Session, ocr_call_number: str, ocr_title: str, limit: int = 5) -> Tuple[Optional[BookMaster], float]:
    """
    [통합 매칭 파이프라인]
    청구기호 기준 후보군과 제목 기준 후보군을 각각 추출하여 통합한 뒤 하이브리드 매칭을 수행합니다.

    반환값: (best_match, highest_score) — 매칭 실패 시에도 최고 점수를 함께 반환합니다.
    """
    # 1. 청구기호 기준 및 제목 기준으로 후보군 검색
    candidates_by_call = get_top_candidates_by_call_number(db, ocr_call_number, limit=limit)
    candidates_by_title = get_top_candidates_by_title(db, ocr_title, limit=limit)
    
    # 2. 두 후보군을 병합하되, ID 중복을 방지하기 위해 dict나 set을 활용하여 unique 리스트 생성
    unique_candidates_map = {}
    
    for book in candidates_by_call:
        unique_candidates_map[book.book_id] = book  # 💡 book.id -> book.book_id 로 수정
        
    for book in candidates_by_title:
        unique_candidates_map[book.book_id] = book  # 💡 book.id -> book.book_id 로 수정
        
    combined_candidates = list(unique_candidates_map.values())
    
    # 후보군이 전혀 없다면 바로 None 반환 (최고 점수 0.0)
    if not combined_candidates:
        return None, 0.0

    # 3. 통합 후보군을 대상으로 하이브리드 퍼지 매칭 실행
    return hybrid_book_matching_with_jamo(ocr_call_number, ocr_title, combined_candidates)