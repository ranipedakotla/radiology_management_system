# # app/utils/pathology_s3.py
# import boto3, uuid
# from app.core.config import settings
#
# s3 = boto3.client(
#     "s3",
#     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#     region_name=settings.AWS_REGION
# )
#
# def upload_bytes(bucket: str, key: str, content: bytes, content_type: str):
#     s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type, ACL="private")
#     return f"s3://{bucket}/{key}"
#
# def presign_url(bucket: str, key: str, expires=3600):
#     return s3.generate_presigned_url(
#         "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
#     )
