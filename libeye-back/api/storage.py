import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# 내부 통신용 환경 변수 (예: api-server가 minio에서 다운로드할 때)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin1234")

# [추가] 프론트엔드(브라우저)가 접근할 외부 주소
EXTERNAL_MINIO_ENDPOINT = "localhost:9000"

def get_s3_client(is_external=False):
    """
    is_external=True이면 브라우저용 서명을 생성하고,
    False이면 도커 내부 통신용 클라이언트를 반환합니다.
    """
    endpoint = EXTERNAL_MINIO_ENDPOINT if is_external else MINIO_ENDPOINT
    
    return boto3.client(
        's3',
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def get_presigned_upload_url(bucket_name: str, object_name: str, expiration=300) -> str:
    # 프론트엔드가 사용할 URL이므로 is_external=True 전달
    s3_client = get_s3_client(is_external=True) 
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
    # 프론트엔드가 이미지를 렌더링할 때 쓸 URL이므로 is_external=True 전달
    s3_client = get_s3_client(is_external=True)
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
