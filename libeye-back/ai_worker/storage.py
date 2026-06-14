import cv2
import numpy as np
import boto3

from config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

s3_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)


def ensure_buckets_exist() -> None:
    try:
        existing = {b["Name"] for b in s3_client.list_buckets()["Buckets"]}
        for bucket in ("original-bucket", "crop-bucket"):
            if bucket not in existing:
                s3_client.create_bucket(Bucket=bucket)
    except Exception as e:
        print(f"MinIO 버킷 초기화 오류 (무시): {e}")


def upload_image(bucket: str, key: str, cv2_img: np.ndarray) -> str | None:
    try:
        # 파일 키의 확장자에 맞게 인코딩 포맷 및 ContentType 선택
        ext = ".png" if key.lower().endswith(".png") else ".jpg"
        content_type = "image/png" if ext == ".png" else "image/jpeg"
        
        _, buf = cv2.imencode(ext, cv2_img)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=buf.tobytes(),
            ContentType=content_type,
        )
        return f"{MINIO_ENDPOINT}/{bucket}/{key}"
    except Exception as e:
        print(f"MinIO 업로드 오류: {e}")
        return None


def download_image(bucket: str, key: str) -> np.ndarray | None:
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        data = response["Body"].read()
        arr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"MinIO 다운로드 오류: {e}")
        return None
