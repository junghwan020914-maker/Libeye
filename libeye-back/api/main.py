from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import os
from celery import Celery # Celery 추가

# 내부 모듈 임포트
from database import get_db, engine, Base
import models
from seed import seed_database
from contextlib import asynccontextmanager
from routers import results

# --- Celery 워커 연결 설정 ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up FastAPI Server...")
    Base.metadata.create_all(bind=engine)
    seed_database() 
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

# --- [수정됨] 세션 생성 시 이미지 Base64를 받아 AI 워커로 전달 ---
class SessionCreateRequest(BaseModel):
    location_id: str
    image_base64: str # 프론트에서 실제 이미지를 받음

@app.post("/api/v1/sessions")
def create_session(req: SessionCreateRequest, db: Session = Depends(get_db)):
    try:
        new_session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        # 1. DB에 세션 저장
        new_session = models.ScanSession(
            session_id=new_session_id,
            location_id=req.location_id,
            image_url="base64_encoded_image", # 임시 텍스트
            status="PENDING"
        )
        db.add(new_session)
        db.commit()
        
        # 2. 진짜 AI 워커(YOLO+Gemma)에게 작업 지시! (Redis 큐로 전송)
        print(f"[{new_session_id}] AI 워커에 작업 전송 중...")
        celery_app.send_task('process_image_task', args=[new_session_id, req.image_base64])
        
        return {"session_id": new_session_id, "status": "PENDING"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
