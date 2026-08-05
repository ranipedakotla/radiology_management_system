import os
import pathlib
from typing import Optional

import boto3
import pdfkit
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.core.security import get_db
from app.models.radiology_report import RadiologyReport
from app.schemas.radiology_report import RadiologyReportCreate

load_dotenv()

router = APIRouter(prefix="/radiology-reports", tags=["Radiology Reports"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION            = os.getenv("AWS_REGION", "ap-south-1")
AWS_BUCKET_NAME       = os.getenv("AWS_BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent.parent / "template"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

# Local hospital logo — adjust path/filename to match where you actually store it
LOGO_PATH = pathlib.Path(__file__).resolve().parent.parent / "static" / "logo.png"

HOSPITAL_NAME = "Sunrise Multispeciality Hospital"

WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH")
pdfkit_config = (
    pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    if WKHTMLTOPDF_PATH
    else pdfkit.configuration()
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def generate_presigned_url(s3_key: str) -> str:
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=3600,
    )


def s3_key_for(report_id: str, patient_uhid: str) -> str:
    return f"radiology-reports/{patient_uhid}/{report_id}.pdf"


def s3_object_exists(s3_key: str) -> bool:
    try:
        s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def get_logo_uri() -> Optional[str]:
    """Local logo file as a file:// URI so wkhtmltopdf loads it without needing network access."""
    if LOGO_PATH.exists():
        return LOGO_PATH.resolve().as_uri()
    return None


def build_context(data: RadiologyReportCreate, page_total: int = 1) -> dict:
    return {
        "hospital": {
            "name": HOSPITAL_NAME,
            "department": data.hospital_department,
            "logo_url": get_logo_uri(),
        },
        "patient": {
            "name": data.patient_name,
            "uhid": data.patient_uhid,
            "age": data.patient_age,
            "gender": data.patient_gender,
            "referring_doctor": data.referring_doctor,
            "department": data.patient_department,
        },
        "study": {
            "date": data.study_date,
            "time": data.study_time,
            "modality": data.modality,
            "test_name": data.test_name,
            "body_part": data.body_part,
        },
        "report": {
            "id": data.report_id,
            "date": data.report_date,
            "time": data.report_time,
        },
        "clinical_history": data.clinical_history,
        "findings": [f.dict() for f in data.findings],
        "impression": data.impression,
        "recommendations": data.recommendations,
        "radiologist": {
            "name": data.radiologist_name,
            "credentials": data.radiologist_credentials,
            "title": data.radiologist_title,
            "reg_no": data.radiologist_reg_no,
        },
        "signature_data_uri": data.signature_data_uri,
        "page": {"current": 1, "total": page_total},
    }


def build_context_from_row(row: RadiologyReport) -> dict:
    return {
        "hospital": {
            "name": HOSPITAL_NAME,
            "department": row.hospital_department,
            "logo_url": get_logo_uri(),
        },
        "patient": {
            "name": row.patient_name,
            "uhid": row.patient_uhid,
            "age": row.patient_age,
            "gender": row.patient_gender,
            "referring_doctor": row.referring_doctor,
            "department": row.patient_department,
        },
        "study": {
            "date": row.study_date,
            "time": row.study_time,
            "modality": row.modality,
            "test_name": row.test_name,
            "body_part": row.body_part,
        },
        "report": {
            "id": row.report_id,
            "date": row.report_date,
            "time": row.report_time,
        },
        "clinical_history": row.clinical_history,
        "findings": row.findings,
        "impression": row.impression,
        "recommendations": row.recommendations,
        "radiologist": {
            "name": row.radiologist_name,
            "credentials": row.radiologist_credentials,
            "title": row.radiologist_title,
            "reg_no": row.radiologist_reg_no,
        },
        "signature_data_uri": row.signature_data_uri,
        "page": {"current": 1, "total": 1},
    }


def render_and_upload(context: dict, report_id: str, patient_uhid: str) -> str:
    template = jinja_env.get_template("radiology_report.html")
    html_out = template.render(**context)

    options = {
        "page-size": "A4",
        "margin-top": "0mm",
        "margin-bottom": "0mm",
        "margin-left": "0mm",
        "margin-right": "0mm",
        "encoding": "UTF-8",
        "enable-local-file-access": "",
    }

    try:
        pdf_bytes = pdfkit.from_string(html_out, False, configuration=pdfkit_config, options=options)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    s3_key = s3_key_for(report_id, patient_uhid)
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ContentDisposition="inline",
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    return s3_key


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/generate")
def generate_report(payload: RadiologyReportCreate, db: Session = Depends(get_db)):
    existing = db.query(RadiologyReport).filter(RadiologyReport.report_id == payload.report_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Report ID {payload.report_id} already exists")

    report = RadiologyReport(
        report_id=payload.report_id,
        hospital_department=payload.hospital_department,
        patient_name=payload.patient_name,
        patient_uhid=payload.patient_uhid,
        patient_age=payload.patient_age,
        patient_gender=payload.patient_gender,
        referring_doctor=payload.referring_doctor,
        patient_department=payload.patient_department,
        study_date=payload.study_date,
        study_time=payload.study_time,
        report_date=payload.report_date,
        report_time=payload.report_time,
        modality=payload.modality,
        test_name=payload.test_name,
        body_part=payload.body_part,
        clinical_history=payload.clinical_history,
        findings=[f.dict() for f in payload.findings],
        impression=payload.impression,
        recommendations=payload.recommendations,
        radiologist_name=payload.radiologist_name,
        radiologist_credentials=payload.radiologist_credentials,
        radiologist_title=payload.radiologist_title,
        radiologist_reg_no=payload.radiologist_reg_no,
        signature_data_uri=payload.signature_data_uri,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    context = build_context(payload)
    s3_key = render_and_upload(context, payload.report_id, payload.patient_uhid)

    report.pdf_s3_key = s3_key
    db.commit()

    pdf_url = generate_presigned_url(s3_key)

    return {"success": True, "data": {"report_id": report.report_id, "pdf_url": pdf_url}}


@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(RadiologyReport).filter(RadiologyReport.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.pdf_s3_key and s3_object_exists(report.pdf_s3_key):
        pdf_url = generate_presigned_url(report.pdf_s3_key)
    else:
        context = build_context_from_row(report)
        s3_key = render_and_upload(context, report.report_id, report.patient_uhid)
        report.pdf_s3_key = s3_key
        db.commit()
        pdf_url = generate_presigned_url(s3_key)

    return {"success": True, "data": {"report_id": report.report_id, "pdf_url": pdf_url}}