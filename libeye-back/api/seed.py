import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 현재 프로젝트의 models와 database 구조를 임포트합니다.
from database import Base
from models import LibraryMaster, BookMaster

# 환경변수에서 DB URL을 가져오거나, 로컬 테스트용 기본값을 사용합니다.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:capstone123@postgres:5432/capstone_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    print("🚀 데이터베이스 Seeding을 시작합니다...")
    
    # 1. 테이블 강제 생성 (만약 없다면 생성)
    # 주의: 프로덕션 환경에서는 Alembic 같은 마이그레이션 툴을 써야하지만, 초기 개발 단계에서는 간편하게 사용합니다.
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 2. 데이터가 이미 존재하는지 확인 (중복 삽입 방지)
        if db.query(LibraryMaster).first():
            print("⚠️ 이미 초기 데이터가 존재합니다. Seeding을 건너뜁니다.")
            return

        # 3. 도서관 공간 데이터(Library_Master) 삽입
        # 사진(book3.jpg)을 2층 인문과학실 A열 1번 서가 3번째 칸으로 가정합니다.
        test_location = LibraryMaster(
            location_id="LOC-A-1-3",
            floor=2,
            room_name="인문과학실",
            section="A열",
            shelf_num=1,
            level_num=3,
            is_active=True
        )
        db.add(test_location)
        db.commit() # 부모 테이블 먼저 커밋

        # 4. 도서 데이터(Book_Master) 삽입
        # 정상적인 배열 순서 (오름차순): 813.6 김12가 -> 813.6 김15나 -> 813.6 박11다 -> 813.6 이21라
        # (테스트의 원활함을 위해, Gemma4가 잘 읽을 만한 일반적인 청구기호 형태로 구성했습니다)
        books = [
            BookMaster(
                book_id="BOOK-001",
                barcode="1000000001",
                call_number="813.6 김12가",
                title="테스트 도서 A",
                author="김작가",
                assigned_loc_id="LOC-A-1-3" # 위에서 만든 위치에 배정
            ),
            BookMaster(
                book_id="BOOK-002",
                barcode="1000000002",
                call_number="813.6 김15나",
                title="테스트 도서 B",
                author="김작가",
                assigned_loc_id="LOC-A-1-3"
            ),
            BookMaster(
                book_id="BOOK-003",
                barcode="1000000003",
                call_number="813.6 박11다",
                title="테스트 도서 C",
                author="박작가",
                assigned_loc_id="LOC-A-1-3"
            ),
            BookMaster(
                book_id="BOOK-004",
                barcode="1000000004",
                call_number="813.6 이21라",
                title="테스트 도서 D",
                author="이작가",
                assigned_loc_id="LOC-A-1-3"
            )
        ]
        
        db.add_all(books)
        db.commit()
        print("✅ 도서관 서가 및 도서 마스터 데이터 초기화 완료!")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
