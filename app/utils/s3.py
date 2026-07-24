import uuid
import boto3
from fastapi import UploadFile
from app.core.settings import settings

session = boto3.Session()
creds = session.get_credentials()

print("Loaded Key:", creds.access_key[:8] + "...")
print("Source:", creds.method)

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

def upload_to_s3(upload: UploadFile, folder: str = "") -> str:
    if not upload:
        return ""

    ext = ""
    if upload.filename and "." in upload.filename:
        ext = "." + upload.filename.rsplit(".", 1)[-1].lower()

    key = f"{folder}/{uuid.uuid4().hex}{ext}" if folder else f"{uuid.uuid4().hex}{ext}"

    #  STREAMING upload (BEST PRACTICE)
    s3_client.upload_fileobj(
        upload.file,
        settings.AWS_BUCKET_NAME,
        key,
        ExtraArgs={
            "ContentType": upload.content_type or "application/octet-stream"
        }
    )

    return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"