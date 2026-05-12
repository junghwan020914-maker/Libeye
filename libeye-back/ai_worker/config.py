import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:capstone123@postgres:5432/libeye_db"
)

MINIO_ENDPOINT = os.getenv("MINIO_URL", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin1234")

OLLAMA_API_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma4:26b")

YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.6"))
OCR_MATCH_THRESHOLD = float(os.getenv("OCR_MATCH_THRESHOLD", "85.0"))
