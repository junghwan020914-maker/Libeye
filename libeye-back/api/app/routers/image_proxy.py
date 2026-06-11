from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os

router = APIRouter(prefix="/api/v1/image-proxy", tags=["Image Proxy"])

# 내부 MinIO 클라이언트 설정 (Docker 네트워크 내부)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin1234")

_s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

@router.get("/{bucket}/{key:path}")
async def proxy_image(bucket: str, key: str):
    """
    MinIO 내부 이미지를 FastAPI가 직접 프록시하여 반환합니다.
    브라우저가 MinIO/ngrok에 직접 접근하지 않아도 됩니다.
    """
    try:
        response = _s3_client.get_object(Bucket=bucket, Key=key)
        content_type = response.get("ContentType", "image/jpeg")
        
        def iter_body():
            for chunk in response["Body"].iter_chunks(chunk_size=1024 * 64):
                yield chunk
        
        return StreamingResponse(
            iter_body(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise HTTPException(status_code=404, detail=f"Image not found: {bucket}/{key}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
