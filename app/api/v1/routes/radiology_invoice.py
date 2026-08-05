import os
import base64
import pathlib
from io import BytesIO
from datetime import datetime
from typing import Optional

import boto3
import qrcode
import pdfkit
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.core.security import get_db
from app.models.radiology_invoice import (
    Patient, Invoice, InvoiceItem, InsuranceDetail, PaymentDetail, BillingSummary
)
from app.schemas.radiology_invoice import InvoiceCreate

load_dotenv()

router = APIRouter(prefix="/invoices", tags=["Invoices"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION            = os.getenv("AWS_REGION", "ap-south-1")
AWS_BUCKET_NAME       = os.getenv("AWS_BUCKET_NAME")
BASE_URL              = os.getenv("BASE_URL", "http://localhost:8000")

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

# WKHTMLTOPDF_PATH now comes from an env var instead of being hardcoded to a
# Windows path. Set WKHTMLTOPDF_PATH in your .env — on Linux this is
# typically just "/usr/bin/wkhtmltopdf" (or omit the var entirely and it
# will use whatever's on PATH).
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
        ExpiresIn=3600,  # 1 hour
    )


def s3_key_for(invoice_no: str, patient_id: int) -> str:
    """Single source of truth for where an invoice's PDF lives in S3.
    Same invoice_no + patient_id -> same key, every time."""
    return f"invoices/{patient_id}/{invoice_no}.pdf"


def s3_object_exists(s3_key: str) -> bool:
    try:
        s3_client.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def generate_qr_data_uri(invoice_no: str) -> str:
    """QR code as base64 data URI — no separate file, embeds directly in the HTML.
    Encodes the STABLE app URL (not the presigned S3 link), so the QR image
    never needs to change even though the S3 link behind it expires hourly."""
    invoice_url = f"{BASE_URL}/invoices/{invoice_no}"
    qr = qrcode.make(invoice_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def get_logo_uri() -> Optional[str]:
    """Local logo file as a file:// URI so wkhtmltopdf loads it without needing network access."""
    if LOGO_PATH.exists():
        return LOGO_PATH.resolve().as_uri()
    return None


def build_context(payload: InvoiceCreate, patient: Patient) -> dict:
    return {
        "hospital": {
            "name": "Arogya Narayan Hospital",
            "tagline": "Premium Healthcare Services",
            "address": "123 Health Avenue, Medical District, Mumbai, MH 400001",
            "phone": "+91 98765 43210",
            "email": "billing@cityarehospital.com",
            "gstin": "27AAAAA0000A1Z5",
            "logo_url": get_logo_uri(),
        },
        "invoice": {
            "invoice_no": payload.invoice_no,
            "date": payload.date,
            "time": payload.time,
            "bill_type": payload.bill_type,
            "notes": payload.notes,
            "terms": payload.terms,
            "generated_by": payload.generated_by,
            "signatory_name": payload.signatory_name,
            "generated_on": datetime.now(),
        },
        "patient": patient,
        "items": payload.items,
        "insurance": payload.insurance,
        "payment": payload.payment,
        "billing": payload.billing,
        "qr_data_uri": generate_qr_data_uri(payload.invoice_no),
    }


def render_and_upload(context: dict, invoice_no: str, patient_id: int) -> str:
    """Render the Jinja2 template, generate the PDF in memory (no local file),
    upload to S3 at the deterministic key, return a presigned URL."""
    template = jinja_env.get_template("invoice_template.html")
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

    s3_key = s3_key_for(invoice_no, patient_id)
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

    return generate_presigned_url(s3_key)


def build_invoice_context(invoice: Invoice, patient: Patient) -> dict:
    """Same shape as build_context(), but sourced from a saved Invoice row
    instead of the incoming payload — used when re-rendering an existing invoice."""
    return {
        "hospital": {
            "name": "Arogya Narayan Hospital",
            "tagline": "Premium Healthcare Services",
            "address": "123 Health Avenue, Medical District, Mumbai, MH 400001",
            "phone": "+91 98765 43210",
            "email": "billing@cityarehospital.com",
            "gstin": "27AAAAA0000A1Z5",
            "logo_url": get_logo_uri(),
        },
        "invoice": {
            "invoice_no": invoice.invoice_no,
            "date": invoice.date,
            "time": invoice.time,
            "bill_type": invoice.bill_type,
            "notes": invoice.notes,
            "terms": invoice.terms,
            "generated_by": invoice.generated_by,
            "signatory_name": invoice.signatory_name,
            "generated_on": invoice.generated_on,
        },
        "patient": patient,
        "items": invoice.items,
        "insurance": invoice.insurance,
        "payment": invoice.payment,
        "billing": invoice.billing,
        "qr_data_uri": generate_qr_data_uri(invoice.invoice_no),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/generate")
def generate_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with id {payload.patient_id} not found")

    existing = db.query(Invoice).filter(Invoice.invoice_no == payload.invoice_no).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Invoice number {payload.invoice_no} already exists")

    # ------------------------------------------------------------------
    # Persist invoice + related rows
    # ------------------------------------------------------------------
    invoice = Invoice(
        invoice_no=payload.invoice_no,
        date=payload.date,
        time=payload.time,
        bill_type=payload.bill_type,
        notes=payload.notes,
        terms=payload.terms,
        generated_by=payload.generated_by,
        signatory_name=payload.signatory_name,
        patient_id=patient.id,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    for item in payload.items:
        db.add(InvoiceItem(invoice_id=invoice.id, **item.dict()))

    if payload.insurance:
        db.add(InsuranceDetail(invoice_id=invoice.id, **payload.insurance.dict()))

    if payload.payment:
        db.add(PaymentDetail(invoice_id=invoice.id, **payload.payment.dict()))

    db.add(BillingSummary(invoice_id=invoice.id, **payload.billing.dict()))
    db.commit()

    # ------------------------------------------------------------------
    # Render + upload PDF
    # (QR code is generated once, inside build_context -> generate_qr_data_uri,
    # and embedded in the PDF itself. No need to build it again here.)
    # ------------------------------------------------------------------
    context = build_context(payload, patient=patient)
    pdf_url = render_and_upload(context, payload.invoice_no, patient.id)

    return {"success": True, "invoice_id": invoice.id, "pdf_url": pdf_url}


@router.get("/{identifier}")
def get_invoice(identifier: str, db: Session = Depends(get_db)):
    """
    This is what the QR code points to. Same invoice_no always resolves to
    the same S3 object, so scanning the QR always opens the same invoice.

    - If the PDF already exists in S3: just mint a fresh presigned URL
      (cheap, no render) and redirect the browser straight to it.
    - If it's somehow missing: render it once, upload, then redirect.
    """
    invoice = db.query(Invoice).filter(Invoice.invoice_no == identifier).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    patient = invoice.patient
    s3_key = s3_key_for(invoice.invoice_no, patient.id)

    if s3_object_exists(s3_key):
        pdf_link = generate_presigned_url(s3_key)
    else:
        context = build_invoice_context(invoice, patient)
        pdf_link = render_and_upload(context, invoice.invoice_no, patient.id)

    return RedirectResponse(url=pdf_link, status_code=307)