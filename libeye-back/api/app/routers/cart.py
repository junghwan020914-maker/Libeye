from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.dependencies import get_db
from app.models.cart import CartSession, CartItem
from app.core.celery_client import celery_app
# MinIO 설정 (구 main.py와 동일한 공용 클라이언트를 core/storage에서 가져옴)
from app.core.storage import s3_client, MINIO_URL

router = APIRouter(prefix="/api/cart", tags=["Cart Sorting"])

@router.post("/upload", status_code=201)
async def upload_cart_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. 파일명 생성
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"cart-{uuid.uuid4().hex[:8]}.{file_ext}"
    
    try:
        # 2. MinIO 'original-bucket'에 이미지 업로드
        content = await file.read()
        s3_client.put_object(
            Bucket='original-bucket',
            Key=file_name,
            Body=content,
            ContentType=file.content_type
        )
        # MinIO 내부 접근 URL
        image_url = f"{MINIO_URL}/original-bucket/{file_name}"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {str(e)}")

    # 3. DB 저장 (image_path 컬럼에 로컬 경로 대신 MinIO URL 저장)
    session = CartSession(image_path=image_url, status="PENDING")
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 4. Celery Worker로 작업 전송 (image_url을 워커로 전달)
    print(f"[Cart] AI 워커에 북카트(Session {session.id}) 분석 요청 전송 중...")
    celery_app.send_task('process_cart_task', args=[session.id, image_url])
    
    return {"session_id": session.id, "status": session.status}

@router.get("/{session_id}")
def get_cart_sorting_result(session_id: int, db: Session = Depends(get_db)):
    session = db.query(CartSession).filter(CartSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Cart session not found")
        
    items = db.query(CartItem).filter(CartItem.session_id == session_id).order_by(CartItem.display_order).all()
    
    # 이미지 URL을 프록시 경로로 변환 (기존 results.py와 유사한 방식 적용 가능)
    # 필요에 따라 프론트엔드가 이미지 표출 시 사용
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
