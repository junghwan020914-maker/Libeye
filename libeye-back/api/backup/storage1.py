import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# docker-compose.yml에서 주입한 환경 변수
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin1234")

def get_s3_client():
    """
    boto3를 사용하여 MinIO(S3 호환) 클라이언트를 초기화합니다.
    """
    return boto3.client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1' # MinIO 기본 리전
    )

def get_presigned_upload_url(bucket_name: str, object_name: str, expiration=300) -> str:
    """
    클라이언트가 MinIO로 직접 업로드할 수 있는 임시 URL을 발급합니다.
    (API 서버 부하 방지용)
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Error generating presigned upload URL: {e}")
        raise
    return response

def get_presigned_download_url(bucket_name: str, object_name: str, expiration=3600) -> str:
    """
    저장된 이미지를 프론트엔드 UI에서 안전하게 보여주기 위한 임시 URL을 발급합니다.
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Error generating presigned download URL: {e}")
        raise
    return response
