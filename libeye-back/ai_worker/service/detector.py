import os
import cv2
import numpy as np

# PyTorch 2.6+ weights_only 보안 정책 우회 (YOLO 구버전 가중치 호환)
os.environ["TORCH_WEIGHTS_ONLY"] = "0"
import torch

_orig_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO
from config import YOLO_CONFIDENCE

# __file__ 은 service/ 안이므로 한 단계 위(ai_worker/)를 기준으로 경로 설정
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOLO_MODEL_PATH = os.path.join(_BASE_DIR, "weights", "best.pt")

try:
    print(f"YOLO 모델 로드 중: {YOLO_MODEL_PATH}")
    yolo_model = YOLO(YOLO_MODEL_PATH, task="segment")
    print("YOLO 모델 로드 완료")
except Exception as e:
    print(f"YOLO 모델 로드 실패: {e}")
    yolo_model = None


def run_detection(img: np.ndarray) -> tuple:
    """
    이미지에서 책등을 탐지한다.
    반환: (boxes, masks) — ultralytics Boxes/Masks 객체
    """
    results = yolo_model(img, conf=YOLO_CONFIDENCE)
    return results[0].boxes, results[0].masks


def crop_spine(img: np.ndarray, box, masks, idx: int) -> np.ndarray:
    """
    단일 책등의 세그멘테이션 마스크를 적용하고 바운딩박스로 크롭한다.
    마스크가 없으면 단순 크롭으로 대체.
    """
    x1, y1, x2, y2 = map(int, box.xyxy[0])

    if masks is not None and len(masks.xy) > idx:
        mask_pts = masks.xy[idx]
        black = np.zeros_like(img)
        cv2.fillPoly(black, [np.int32(mask_pts)], (255, 255, 255))
        segmented = cv2.bitwise_and(img, black)
        return segmented[y1:y2, x1:x2]

    return img[y1:y2, x1:x2]
