import os
from celery import Celery

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "libeye_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    result_expires=3600,
    task_acks_late=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=False,
)

# 🚨 수정됨: 단일 이미지 처리 -> 세션 단위 다중 이미지 처리로 Task 이름 및 파라미터 변경
# ai_worker/pipeline.py에 정의된 @celery_app.task(name="process_session_task")와 이름을 일치시킵니다.
@celery_app.task(bind=True, name="process_session_task")
def process_scan_session(self, session_id: str):
    """
    MinIO에 업로드된 다중 이미지(세션)를 가져와서 객체 탐지 및 병합 처리를 수행하는 비동기 작업.
    (API 서버에서는 껍데기만 호출하고, 실제 처리는 AI 워커 노드에서 담당)
    """
    pass
