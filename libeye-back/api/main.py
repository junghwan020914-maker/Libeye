from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from celery import Celery 
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

# --- [수정됨] MinIO 클라이언트 설정 (lifespan에서 에러 방지를 위해 위로 이동) ---
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id="admin",
    aws_secret_access_key="admin1234"
)

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

# --- [수정됨] 단일 Base64 -> 다중 파일(Multipart Form) 업로드 처리로 변경 ---
@app.post("/api/v1/sessions")
async def create_session(
    location_id: str = Form(...), 
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db)
):
    try:
        new_session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        # 1. DB에 세션 저장 (이제 ScanSession 자체에는 image_url이 없습니다)
        new_session = models.ScanSession(
            session_id=new_session_id,
            location_id=location_id,
            status="PENDING"
        )
        db.add(new_session)
        
        # 2. 전송받은 여러 장의 파일들을 순서대로 처리하여 MinIO 및 DB(ScanImage)에 저장
        for index, file in enumerate(files):
            # 파일 확장자 추출 및 파일명 생성
            ext = os.path.splitext(file.filename)[1]
            if not ext:
                ext = ".jpg" # 확장자가 없는 경우 기본값
            
            image_id = f"img-{uuid.uuid4().hex[:6]}"
            file_name = f"{new_session_id}/{image_id}{ext}"
            
            # MinIO 업로드 (비동기로 파일 읽기)
            content = await file.read()
            s3_client.put_object(
                Bucket='original-bucket',
                Key=file_name,
                Body=content,
                ContentType=file.content_type
            )
            
            # 생성된 실제 MinIO URL
            original_url = f"{MINIO_URL}/original-bucket/{file_name}"
            
            # 🚨 핵심: ScanImage 레코드 생성 (왼쪽부터의 순서 저장)
            new_image = models.ScanImage(
                image_id=image_id,
                session_id=new_session_id,
                image_url=original_url,
                sequence_order=index  # 배열로 들어온 순서대로 0, 1, 2... 저장
            )
            db.add(new_image)
            
        db.commit()
        
        # 3. Redis 큐에는 이제 개별 파일이 아닌 '세션 ID' 하나만 전송
        print(f"[{new_session_id}] AI 워커에 {len(files)}개 이미지 분석 요청 전송 중...")
        celery_app.send_task('process_session_task', args=[new_session_id])
        
        return {
            "session_id": new_session_id, 
            "image_count": len(files),
            "status": "PENDING"
        }
    except Exception as e:
        db.rollback()
        print(f"업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
