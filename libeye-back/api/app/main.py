from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

# 내부 모듈 임포트
from app.database import engine, Base
from app import models  # Base.metadata에 전체 테이블이 등록되도록 import
from app.core.seed import seed_database
from app.core.storage import s3_client
from app.routers import sessions, results, image_proxy, locations, history, map, analytics, search, cart

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up FastAPI Server...")
    Base.metadata.create_all(bind=engine)

    # 🌟 [경량 마이그레이션] create_all은 기존 테이블에 컬럼을 추가하지 못하므로,
    #    이미 존재하는 DB에도 highest_score 컬럼이 생기도록 멱등(idempotent) ALTER 실행
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE scan_result_detail "
                "ADD COLUMN IF NOT EXISTS highest_score DECIMAL(5,2) DEFAULT 0"
            ))
    except Exception as e:
        print("highest_score 컬럼 마이그레이션 확인 중 오류:", e)

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

app.include_router(sessions.router)  # 기존 main.py에 있던 업로드 엔드포인트 분리
app.include_router(results.router)
app.include_router(image_proxy.router)
app.include_router(locations.router)
app.include_router(history.router)
app.include_router(map.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(cart.router)  # 신규 북카트 라우터 추가
