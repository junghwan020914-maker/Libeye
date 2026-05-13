from typing import Iterable, Optional

from thefuzz import fuzz
from jamo import h2j, j2hcj

from models import BookMaster

WEIGHT_CALL_NUM = 0.8
WEIGHT_TITLE = 0.2
MATCH_THRESHOLD = 80.0


def decompose_korean(text: str) -> str:
    """한글 텍스트를 초성·중성·종성(자소) 단위로 분해."""
    if not text:
        return ""
    try:
        return j2hcj(h2j(text))
    except Exception:
        return text


def hybrid_book_matching_with_jamo(
    ocr_call_number: str,
    ocr_title: str,
    db_candidates: Iterable[BookMaster],
) -> Optional[BookMaster]:
    """
    청구기호(일반 퍼지)와 도서명(자소 분리 퍼지)을 가중합한 하이브리드 매칭.
    - 청구기호 80% : ratio / partial_ratio / token_sort_ratio 중 최댓값
    - 도서명   20% : 자소 분리 후 token_sort_ratio
    임계값 미만이면 None.
    """
    clean_call = (ocr_call_number or "").strip()
    if not clean_call:
        return None

    ocr_title_jamo = decompose_korean(ocr_title)

    best_match: Optional[BookMaster] = None
    highest_score = 0.0

    for book in db_candidates:
        call_num_score = max(
            fuzz.ratio(clean_call, book.call_number),
            fuzz.partial_ratio(clean_call, book.call_number),
            fuzz.token_sort_ratio(clean_call, book.call_number),
        )
        title_score = fuzz.token_sort_ratio(
            ocr_title_jamo,
            decompose_korean(book.title),
        )
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
            f"[매칭 성공] '{clean_call}' / '{ocr_title}' → "
            f"'{best_match.call_number}' / '{best_match.title}' "
            f"(점수 {highest_score:.1f})"
        )
        return best_match

    print(f"[매칭 실패] '{clean_call}' / '{ocr_title}' (최고 점수 {highest_score:.1f} < {MATCH_THRESHOLD})")
    return None
