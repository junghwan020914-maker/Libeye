from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import uuid
import os
import boto3

from database import get_db
from models_cart import CartSession, CartItem
from worker import celery_app

router = APIRouter(prefix="/api/cart", tags=["Cart Sorting"])

# MinIO 설정 (main.py의 설정과 동일하게 구성)
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id="admin",
    aws_secret_access_key="admin1234"
)

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
