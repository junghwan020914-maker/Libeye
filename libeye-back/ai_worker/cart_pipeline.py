from .service.detector import BookDetector  # 기존 모델 검출 재사용
from .service.ocr import BookOCR            # 기존 OCR 재사용
from .service.matcher import BookMatcher    # 기존 매칭 로직 재사용
from .service.cart_sorter import CartSorter # 신규 정렬 모듈
from .database import SessionLocal
from .models_cart import CartSession, CartItem

def process_cart_job(session_id: int, image_path: str):
    """
    북카트 도서 분류 처리를 위한 독립적 파이프라인 함수
    """
    db = SessionLocal()
    try:
        # 1. 진행 상태로 업데이트
        session = db.query(CartSession).filter(CartSession.id == session_id).first()
        if not session:
            return
        session.status = "PROCESSING"
        db.commit()

        # 2. 기존 AI 레이어 활용하여 가치 추출 (결합 방지 목적의 단순 호출)
        # 이미지 내 도서 등표 영역(Bounding Box) 검출
        boxes = BookDetector.detect_books(image_path)
        
        raw_books = []
        for box in boxes:
            # 텍스트 OCR 인식
            ocr_text = BookOCR.recognize_text(image_path, box)
            if ocr_text:
                # 데이터베이스 내 실제 도서 매칭 검증
                book_meta = BookMatcher.match_book(ocr_text)
                raw_books.append({
                    "title": book_meta.get("title", "알 수 없는 도서"),
                    "call_number": ocr_text,
                    "shelf_location": book_meta.get("shelf_location", "미지정 구역")
                })

        # 3. 새로운 도서 정렬 서비스 수행
        sorted_books = CartSorter.sort_by_call_number(raw_books)

        # 4. 정렬 순서(display_order) 보존하여 영속화
        for index, book in enumerate(sorted_books):
            item = CartItem(
                session_id=session_id,
                title=book["title"],
                call_number=book["call_number"],
                shelf_location=book["shelf_location"],
                display_order=index + 1  # 1부터 시작하는 정렬 가이드 순서
            )
            db.add(item)

        session.status = "SUCCESS"
        db.commit()

    except Exception as e:
        db.rollback()
        session = db.query(CartSession).filter(CartSession.id == session_id).first()
        if session:
            session.status = "FAILED"
            db.commit()
        print(f"[ERROR] Cart Pipeline processing failed: {str(e)}")
    finally:
        db.close()