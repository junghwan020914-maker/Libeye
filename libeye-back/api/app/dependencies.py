from app.database import SessionLocal

def get_db():
    """
    FastAPI 의존성 주입(Dependency Injection)을 위한 DB 세션 제너레이터입니다.
    API 요청이 들어올 때마다 새로운 DB 세션을 열고,
    요청 처리가 끝나면(예외가 발생하더라도) 안전하게 세션을 닫아줍니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
