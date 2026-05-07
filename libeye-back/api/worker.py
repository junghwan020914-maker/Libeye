import os
from celery import Celery

# docker-compose.yml에서 주입한 Redis URL을 사용합니다.
# 브로커(Broker)와 결과 백엔드(Backend) 모두 동일한 Redis 인스턴스를 사용하도록 설정합니다.
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Celery 인스턴스 생성 (이름: 'libeye_tasks')
celery_app = Celery(
    "libeye_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery 세부 설정
celery_app.conf.update(
    # 작업 결과 저장 만료 시간 (예: 1시간)
    result_expires=3600,
    
    # 늦은 확인(Late Acknowledgment) 활성화: 
    # 워커가 작업을 도중에 실패하거나 강제 종료되었을 때(예: OOM), 
    # 메시지가 유실되지 않고 다른 워커가 재시도할 수 있도록 합니다. (안정성 강화)
    task_acks_late=True,
    
    # 작업 직렬화 방식 (JSON 사용)
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 타임존 설정
    timezone='Asia/Seoul',
    enable_utc=False,
)

# --- [비동기 작업 정의 (Task)] ---
# 실제 AI 추론 로직은 'ai_worker' 컨테이너에서 실행되지만, 
# API 서버가 작업을 호출(Delay)할 수 있도록 함수 시그니처를 등록해둡니다.

@celery_app.task(bind=True, name="process_scan_image")
def process_scan_image(self, session_id: str, location_id: str, image_object_name: str):
    """
    MinIO에 업로드된 이미지를 가져와서 객체 탐지 및 VLM 처리를 수행하는 비동기 작업.
    (API 서버에서는 껍데기만 호출하고, 실제 처리는 AI 워커 노드에서 담당)
    """
    # API 서버 단에서는 이 함수 내부 로직이 실행되지 않습니다.
    # 추후 AI 워커 폴더(ai_worker/)에 동일한 이름(name)의 태스크를 등록하여 
    # 실제 Gemma4 파이프라인 로직을 구현하게 됩니다.
    pass
