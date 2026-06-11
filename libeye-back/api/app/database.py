import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# docker-compose.yml에서 주입한 환경변수를 가져옵니다. 
# 로컬 테스트 시 기본값으로 'libeye_db' 연결 정보를 사용합니다.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:libeye_admin_pwd@postgres:5432/libeye_db"
)

# SQLAlchemy 엔진 생성
# 도커 환경의 PostgreSQL과 통신하는 핵심 객체입니다.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# DB 세션 팩토리 생성
# autocommit=False: 트랜잭션을 수동으로 관리하여 안전성을 높입니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 모델의 기본(Base) 클래스 생성
# 이 Base 클래스를 app/models/ 의 각 테이블 클래스가 상속받게 됩니다.
Base = declarative_base()
