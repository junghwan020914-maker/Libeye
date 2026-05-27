from collections import Counter
from typing import Optional


def detect_misplacements(
    books: list[dict],
    location_id: Optional[str] = None,
) -> tuple[list[dict], Optional[str]]:
    """
    1차 필터: 책장 기반 오배열 검사
    2차 필터: expected_order 기반 LIS 순서 검사

    books       : pipeline.py의 scanned_results (x좌표 정렬 완료)
                  각 항목에 matched_book_id, assigned_loc_id, expected_order 포함
    location_id : 세션의 서가 ID
                  - 있으면 해당 서가 기준으로 1차 필터
                  - 없으면 매칭된 책들의 다수결로 현재 서가 추론
    """
    if not books:
        return books, location_id

    # ── 1차 필터: 책장 기반 ──────────────────────────────────────────────

    current_loc = _resolve_location(books, location_id)

    if current_loc is None:
        # 매칭된 책이 하나도 없어 서가를 알 수 없음 → 전부 UNKNOWN
        for book in books:
            book["status"] = "UNKNOWN"
        return books, None

    for book in books:
        if not _is_matched(book):
            book["status"] = "UNKNOWN"
        elif book["assigned_loc_id"] != current_loc:
            book["status"] = "MISPLACED"
        # 통과한 책은 status 미설정 → 2차 필터로 넘어감

    # ── 2차 필터: expected_order 기반 LIS ────────────────────────────────

    # 1차 통과 (status 미설정) 책들만 대상, 원본 인덱스 보존
    candidates = [(i, b) for i, b in enumerate(books) if "status" not in b]

    if candidates:
        correct_candidate_indices = _lis_non_decreasing(
            [b["expected_order"] for _, b in candidates]
        )
        for ci, (orig_idx, _) in enumerate(candidates):
            books[orig_idx]["status"] = "MATCH" if ci in correct_candidate_indices else "MISPLACED"

    _log(books, current_loc)
    return books, current_loc


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────

def _resolve_location(books: list[dict], location_id: Optional[str]) -> Optional[str]:
    """
    현재 서가를 결정한다.
    location_id가 주어지면 그대로 사용, 없으면 매칭된 책들의 다수결로 추론.
    """
    if location_id:
        return location_id

    matched_locs = [b["assigned_loc_id"] for b in books if _is_matched(b)]
    if not matched_locs:
        return None

    return Counter(matched_locs).most_common(1)[0][0]


def _is_matched(book: dict) -> bool:
    """DB 매칭에 성공했고 expected_order가 존재하는 책인지 확인."""
    return (
        book.get("matched_book_id") is not None
        and book.get("assigned_loc_id") is not None
        and book.get("expected_order") is not None
    )


def _lis_non_decreasing(orders: list[int]) -> set[int]:
    """
    정수 리스트에서 단조 비감소(non-decreasing, <=) LIS 인덱스 집합을 반환.
    복본(동일 청구기호 연속 배치)을 오류로 처리하지 않기 위해 <= 비교 사용.
    """
    n = len(orders)
    dp = [1] * n
    prev = [-1] * n

    for i in range(1, n):
        for j in range(i):
            if orders[j] <= orders[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j

    # 가장 긴 수열의 끝 인덱스 (뒤에서부터 탐색해 안정성 확보)
    max_len = max(dp)
    end = next(i for i in range(n - 1, -1, -1) if dp[i] == max_len)

    # 역추적으로 LIS 구성 인덱스 수집
    correct: set[int] = set()
    cur = end
    while cur >= 0:
        correct.add(cur)
        cur = prev[cur]

    return correct


def _log(books: list[dict], current_loc: str) -> None:
    counts = Counter(b.get("status") for b in books)
    print(
        f"[오배열 판별] 서가={current_loc} | "
        f"MATCH={counts['MATCH']} "
        f"MISPLACED={counts['MISPLACED']} "
        f"UNKNOWN={counts['UNKNOWN']}"
    )
