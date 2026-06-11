import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
# 🚨 수정됨: 새로 생성한 ScanImage 모델을 import에 추가하여 테이블이 정상 생성되도록 함
from app.models import LibraryMaster, BookMaster, ScanSession, ScanImage, ScanResultDetail

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:capstone123@postgres:5432/capstone_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    print("🚀 데이터베이스 Seeding을 시작합니다...")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        if db.query(LibraryMaster).first():
            print("⚠️ 이미 초기 데이터가 존재합니다. Seeding을 건너뜁니다.")
            return

        # 이 파일이 app/core/ 로 이동하면서 seed-data.sql은 두 단계 위(api 루트)에 위치합니다.
        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        sql_file_path = os.path.join(api_root, "seed-data.sql")
        
        if not os.path.exists(sql_file_path):
            print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file_path}")
            return

        print(f"📂 {sql_file_path} 파일에서 데이터를 읽어옵니다...")
        
        with open(sql_file_path, "r", encoding="utf-8") as file:
            sql_script = file.read()
        
        for statement in sql_script.split(';'):
            if statement.strip():
                db.execute(text(statement))
        
        db.commit()
        print("✅ 도서관 서가 및 도서 마스터 데이터 초기화 완료!")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
