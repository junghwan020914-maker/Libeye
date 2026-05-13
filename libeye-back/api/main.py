from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import os
from celery import Celery # Celery 추가
import base64
import boto3

# 내부 모듈 임포트
from database import get_db, engine, Base
import models
from seed import seed_database
from contextlib import asynccontextmanager
from routers import results, image_proxy, locations, history, map, analytics

# --- Celery 워커 연결 설정 ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up FastAPI Server...")
    Base.metadata.create_all(bind=engine)
    seed_database() 

    # 서버 켜질 때 original-bucket 미리 생성
    try:
        buckets = [b['Name'] for b in s3_client.list_buckets()['Buckets']]
        if 'original-bucket' not in buckets:
            s3_client.create_bucket(Bucket='original-bucket')
    except Exception as e:
        print("MinIO 버킷 확인 오류:", e)

    yield
    print("Shutting down FastAPI Server...")

app = FastAPI(title="스마트 서고 관리 시스템 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(results.router)
app.include_router(image_proxy.router)
app.include_router(locations.router)
app.include_router(history.router)
app.include_router(map.router)
app.include_router(analytics.router)

# --- [수정됨] 세션 생성 시 이미지 Base64를 받아 AI 워커로 전달 ---
class SessionCreateRequest(BaseModel):
    location_id: str
    image_base64: str # 프론트에서 실제 이미지를 받음

@app.post("/api/v1/sessions")
def create_session(req: SessionCreateRequest, db: Session = Depends(get_db)):
    try:
        new_session_id = f"session-{uuid.uuid4().hex[:8]}"
        original_file_name = f"{new_session_id}_original.jpg"
        
        # 1. Base64 이미지를 디코딩하여 MinIO에 즉시 업로드! (핵심)
        image_bytes = base64.b64decode(req.image_base64)
        s3_client.put_object(
            Bucket='original-bucket',
            Key=original_file_name,
            Body=image_bytes,
            ContentType='image/jpeg'
        )
        # 생성된 실제 MinIO URL
        original_url = f"{MINIO_URL}/original-bucket/{original_file_name}"
        
        # 2. DB에 세션 저장 (이제 가짜 텍스트 대신 진짜 URL을 저장합니다)
        new_session = models.ScanSession(
            session_id=new_session_id,
            location_id=req.location_id,
            image_url=original_url, 
            status="PENDING"
        )
        db.add(new_session)
        db.commit()
        
        # 3. Redis 큐에는 무거운 이미지 대신 '파일 이름'만 전송!
        print(f"[{new_session_id}] AI 워커에 작업 전송 중...")
        celery_app.send_task('process_image_task', args=[new_session_id, original_file_name])
        
        return {"session_id": new_session_id, "status": "PENDING"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- [추가] MinIO 클라이언트 설정 ---
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id="admin",
    aws_secret_access_key="admin1234"
)