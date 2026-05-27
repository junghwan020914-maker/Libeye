from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import uuid
import os
from ..database import get_db
from ..models_cart import CartSession, CartItem

router = APIRouter(prefix="/api/cart", tags=["Cart Sorting"])

UPLOAD_DIR = "static/cart_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=201)
async def upload_cart_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. 고유 파일명 생성 및 이미지 저장
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File write failed: {str(e)}")

    # 2. 북카트 세션 레코드 생성 (초기 상태: PENDING)
    session = CartSession(image_path=file_path, status="PENDING")
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 3. AI 백그라운드 워커 파이프라인 트리거
    # (Celery 환경일 경우 .delay() 형태로 변환 가능, 여기서는 프로젝트 기본 구조에 맞춰 구성)
    from ai_worker.cart_pipeline import process_cart_job
    background_tasks.add_task(process_cart_job, session.id, file_path)
    
    return {"session_id": session.id, "status": session.status}

@router.get("/{session_id}")
def get_cart_sorting_result(session_id: int, db: Session = Depends(get_db)):
    session = db.query(CartSession).filter(CartSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Cart session not found")
        
    # 정렬 순서(display_order)에 맞추어 도서 반환
    items = db.query(CartItem).filter(CartItem.session_id == session_id).order_by(CartItem.display_order).all()
    
    return {
        "session_id": session.id,
        "status": session.status,
        "image_path": session.image_path,
        "created_at": session.created_at,
        "books": [
            {
                "id": item.id,
                "title": item.title,
                "call_number": item.call_number,
                "shelf_location": item.shelf_location,
                "display_order": item.display_order
            } for item in items
        ]
    }