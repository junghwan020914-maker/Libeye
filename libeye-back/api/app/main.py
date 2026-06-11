from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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
