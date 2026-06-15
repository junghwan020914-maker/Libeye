"""
작업 단계별 소요시간 측정용 유틸리티.

디버깅 시 어떤 단계(다운로드/YOLO/OCR/매칭/DB저장 등)에서
시간이 오래 걸리는지 확인하기 위해 사용한다.

사용 예시:
    from timing import get_logger, StageTimer

    log = get_logger()
    timer = StageTimer(session_id)

    with timer.stage("YOLO 탐지"):
        boxes, masks = run_detection(img)

    # 루프 안에서 같은 라벨을 여러 번 호출하면 자동으로 누적된다.
    for crop in crops:
        with timer.stage("OCR"):
            ocr_result = extract_text_with_gemma(b64)

    timer.summary()   # 단계별 누적 소요시간 요약 출력
"""

import time
import logging
from contextlib import contextmanager

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "libeye") -> logging.Logger:
    """타임스탬프가 포함된 로거를 반환한다. (핸들러 중복 추가 방지)"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Celery 루트 로거로 중복 전파 방지
    return logger


_logger = get_logger()


class StageTimer:
    """
    한 작업(세션/잡) 내 여러 단계의 소요시간을 측정·누적한다.

    - stage(label) 컨텍스트로 감싼 구간의 소요시간을 측정한다.
    - 같은 label을 여러 번 호출하면 횟수와 시간을 누적한다.
    - summary()로 전체 + 단계별 분석 결과를 한 번에 출력한다.
    """

    def __init__(self, tag: str):
        self.tag = tag
        self._t0 = time.perf_counter()
        # label -> {"total": 누적초, "count": 호출횟수}
        self._stats: dict[str, dict[str, float]] = {}
        # category(YOLO/OCR/IO) -> 누적초. DB에 그룹별로 저장하기 위함.
        self._categories: dict[str, float] = {}

    def elapsed(self) -> float:
        """시작 시점부터 현재까지의 총 경과 시간(초)을 반환한다."""
        return round(time.perf_counter() - self._t0, 2)

    def category_total(self, category: str) -> float:
        """지정한 카테고리(YOLO/OCR/IO)의 누적 소요시간(초)을 반환한다."""
        return round(self._categories.get(category, 0.0), 2)

    @contextmanager
    def stage(self, label: str, category: str | None = None):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            stat = self._stats.setdefault(label, {"total": 0.0, "count": 0})
            stat["total"] += elapsed
            stat["count"] += 1
            # category가 주어지면 그룹별 누적치도 함께 집계 (YOLO/OCR/IO)
            if category:
                self._categories[category] = (
                    self._categories.get(category, 0.0) + elapsed
                )
            _logger.info(f"[{self.tag}] ⏱ {label}: {elapsed:.2f}s")

    def summary(self):
        total = time.perf_counter() - self._t0
        _logger.info(f"[{self.tag}] ===== 단계별 소요시간 요약 (총 {total:.2f}s) =====")
        # 오래 걸린 순으로 정렬해 병목을 한눈에 파악
        for label, stat in sorted(
            self._stats.items(), key=lambda kv: kv[1]["total"], reverse=True
        ):
            cnt = int(stat["count"])
            tot = stat["total"]
            avg = tot / cnt if cnt else 0.0
            pct = (tot / total * 100) if total else 0.0
            _logger.info(
                f"[{self.tag}]   - {label}: {tot:.2f}s "
                f"({pct:.0f}%, {cnt}회, 평균 {avg:.2f}s)"
            )
        _logger.info(f"[{self.tag}] ============================================")
