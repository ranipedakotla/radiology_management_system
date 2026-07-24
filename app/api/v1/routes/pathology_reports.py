from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.core.security import async_get_db
from app.core.settings import settings
from app.models.pathology_orders import Report
import boto3

router = APIRouter(prefix="/reports", tags=["Reports"])

def _s3():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

@router.get("/verify/{token}")
async def verify_report(token: str, db: AsyncSession = Depends(async_get_db)):
    rep = db.query(Report).filter(Report.qr_code_token == token, Report.is_current == True).one_or_none()  # noqa
    if not rep:
        raise HTTPException(404, "Report not found or expired")

    # return a fresh presigned URL each time
    s3 = _s3()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": rep.s3_key},
        ExpiresIn=settings.REPORT_URL_EXPIRES,
    )
    # Redirect to the file for convenience (or return JSON if you prefer)
    return RedirectResponse(url)
