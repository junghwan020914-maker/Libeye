from typing import Iterable, Optional

from thefuzz import fuzz
from jamo import h2j, j2hcj

from models import BookMaster

WEIGHT_CALL_NUM = 0.8
WEIGHT_TITLE = 0.2
MATCH_THRESHOLD = 80.0


def decompose_korean(text: str) -> str:
    """한글 텍스트를 초성·중성·종성(자소) 단위로 분해."""
    # 💡 방어 로직: 텍스트가 비어있거나, LLM 환각으로 인해 bool 타입이 들어오면 빈 문자열 반환
    if not text or isinstance(text, bool):
        return ""
    
    # 확실하게 문자열로 강제 변환
    text_str = str(text)
    try:
        return j2hcj(h2j(text_str))
    except Exception:
        return text_str


def hybrid_book_matching_with_jamo(
    ocr_call_number: str,
    ocr_title: str,
    db_candidates: Iterable[BookMaster],
) -> Optional[BookMaster]:
    """
    [2단계 검색] 청구기호(일반 퍼지)와 도서명(자소 분리 퍼지)을 가중합한 하이브리드 매칭.
    """
    # 💡 방어 로직: bool 타입이면 빈 문자열로 치환, 아니면 문자열로 변환 후 공백 제거
    clean_call = "" if isinstance(ocr_call_number, bool) else str(ocr_call_number or "").strip()
    
    if not clean_call:
        return None

    # 제목 역시 동일한 방어 로직 적용
    safe_title = "" if isinstance(ocr_title, bool) else str(ocr_title or "").strip()
    ocr_title_jamo = decompose_korean(safe_title)

    best_match: Optional[BookMaster] = None
    highest_score = 0.0

    for book in db_candidates:
        # 1. 청구기호 점수 계산
        call_num_score = max(
            fuzz.ratio(clean_call, book.call_number),
            fuzz.partial_ratio(clean_call, book.call_number),
            fuzz.token_sort_ratio(clean_call, book.call_number),
        )
        
        # 2. 제목 점수 계산 (길이 차이 극복을 위해 partial_ratio 추가)
        db_title_jamo = decompose_korean(book.title)
        
        title_score = max(
            fuzz.token_sort_ratio(ocr_title_jamo, db_title_jamo),
            fuzz.partial_ratio(ocr_title_jamo, db_title_jamo)
        )
        
        # 3. 최종 가중합 산출
        final_score = call_num_score * WEIGHT_CALL_NUM + title_score * WEIGHT_TITLE

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
        return best_match

    print(f"[매칭 실패] '{clean_call}' / '{safe_title}' (최고 점수 {highest_score:.1f} < {MATCH_THRESHOLD})")
    return None