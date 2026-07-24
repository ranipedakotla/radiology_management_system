from datetime import datetime

import pdfkit
# import qrcode
import base64
import pathlib
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from app.core.security import get_db, require_roles
from app.models.appointments import Appointment
from app.models.auth import User
from app.models.invoice_models import HospitalInvoice, HospitalInvoiceItem
from app.models.invoice_models import HospitalInvoicePayment
from app.schemas.invoice_schemas import InvoiceCreate
from dotenv import load_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.core.settings import settings
import qrcode
import qrcode

print("QRCODE FILE:", qrcode.__file__)
print("QRCODE DIR:", dir(qrcode))
print("QRCODE VERSION:", getattr(qrcode, "__version__", "No version"))
load_dotenv()

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def generate_presigned_url(s3_key: str) -> str:
    """
    Builds:
    https://pathologyone.s3.ap-south-1.amazonaws.com/invoices/10/INV-2026-00048.pdf?AWSAccessKeyId=...&Signature=...&Expires=...
    Expires in 1 hour, unique token every call.
    """
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_BUCKET_NAME,
            "Key"   : s3_key,         # invoices/10/INV-2026-00048.pdf
        },
        ExpiresIn=3600   # 1 hour
    )

# def generate_invoice_number(db: Session) -> str:
#     from datetime import datetime
#     year = datetime.now().year
#     # Count invoices this year and increment
#     count = db.query(HospitalInvoice).filter(
#         HospitalInvoice.invoice_number.like(f"INV-{year}-%")
#     ).count()
#     return f"INV-{year}-{str(count + 1).zfill(5)}"

@router.post("/create")
def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("superadmin", "billing", "receptionist")
    ),
):
    appointment = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=404,
            detail=f"Appointment {data.appointment_id} not found"
        )

    # 2. Check invoice doesn't already exist for this appointment
    existing_invoice = db.query(HospitalInvoice).filter(HospitalInvoice.appointment_id == data.appointment_id).first()
    if existing_invoice:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice already exists for appointment {data.appointment_id} — invoice number: {existing_invoice.invoice_number}"
        )

    # ----------------------------
    # Calculate totals across all items
    # ----------------------------
    subtotal = sum(item.qty * item.unit_price for item in data.items)

    discount_value = subtotal * (data.discount_pct / 100)
    taxable_amount = subtotal - discount_value
    tax_value = taxable_amount * (data.tax_pct / 100)

    total = taxable_amount + tax_value
    due = total - data.paid


    # ----------------------------
    # Save Invoice
    # ----------------------------
    invoice = HospitalInvoice(
        appointment_id=data.appointment_id,
        invoice_number="TEMP",  # ← auto generated
        currency=data.currency,

        discount_pct=data.discount_pct,
        discount_reason=data.discount_reason,  # ← new
        tax_pct=data.tax_pct,
        paid=data.paid,

        referral_name=data.referral_name,  # ← new
        referral_amount=data.referral_amount,  # ← new

        patient_name=data.patient_name,
        patient_gender=data.patient_gender,
        patient_dob=data.patient_dob,

        subtotal=subtotal,
        discount_value=discount_value,
        tax_value=tax_value,
        total=total,
        due=due
    )


    db.add(invoice)
    db.flush()
    invoice.invoice_number = f"INV-{datetime.now().year}-{invoice.id:05d}"

    db.commit()
    db.refresh(invoice)

    # ----------------------------
    # Save Invoice Items
    # ----------------------------
    db_items = []
    for item in data.items:
        line_total = item.qty * item.unit_price
        db_item = HospitalInvoiceItem(
            invoice_id=invoice.id,
            description=item.description,
            qty=item.qty,
            unit_price=item.unit_price,
            line_total=round(line_total, 2)
        )
        db.add(db_item)
        db_items.append(db_item)

    # ----------------------------
    # Save Payments
    # ----------------------------
    db_payments = []
    if data.payments:
        for payment in data.payments:
            db_payment = HospitalInvoicePayment(
                invoice_id=invoice.id,
                amount=payment.amount,
                method=payment.method,
                ref=payment.ref,
                date=payment.date
            )
            db.add(db_payment)
            db_payments.append(db_payment)

    db.commit()

    # ----------------------------
    # Generate QR Code
    # ----------------------------
    invoice_url = f"{settings.BASE_URL}/invoice/{invoice.invoice_number}"
    print(invoice_url)
    qr = qrcode.make(invoice_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_data_uri = (
        "data:image/png;base64,"
        + base64.b64encode(buffer.getvalue()).decode()
    )

    # ----------------------------
    # Render HTML Template
    # ----------------------------
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("invoice.html")

    # logo_path = pathlib.Path("app/static/logo.png").resolve().as_uri()
    logo_path = pathlib.Path("C:/Users/SecurXperts/Downloads/logo.png").resolve().as_uri()

    html = template.render(
        invoice=invoice,

        lab={
            "name": "CARE HOSPITAL",
            "phone": "9876543210",
            "email": "care@hospital.com",
            "address": "Madhapur, Hyderabad"
        },

        patient={
            "name": invoice.patient_name,
            "gender": invoice.patient_gender,
            "dob": invoice.patient_dob
        },

        lines=[
            {
                "desc": i.description,
                "qty": i.qty,
                "unit_price": i.unit_price,
                "line_total": i.line_total
            }
            for i in db_items
        ],

        payments=[
            {
                "amount": p.amount,
                "method": p.method,
                "ref": p.ref,
                "date": p.date
            }
            for p in db_payments
        ],

        qr_data_uri=qr_data_uri,
        hospital_logo=logo_path
    )

    # ----------------------------
    # Generate PDF → upload to S3
    # ----------------------------
    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )
    options = {
        "enable-local-file-access": ""
    }

    # Generate PDF as bytes (no local file)
    pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)


    # Upload to S3
    s3_key = f"invoices/{invoice.id}/{invoice.invoice_number}.pdf"
    try:
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ContentDisposition="inline",
        )
        print(f" Uploaded: {s3_key}")
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    # ← SAVE KEY TO DB
    invoice.file_key = s3_key
    db.commit()
    for item in db_items:
        db.refresh(item)

    for payment in db_payments:
        db.refresh(payment)

    db.refresh(invoice)

    print(f" pdf_key saved: {invoice.file_key}")  # verify it saved

    # Generate presigned URL
    pdf_link = generate_presigned_url(s3_key)

    return {
        "message": "Invoice created successfully",
        "invoice_id": invoice.id,
        "pdf_link": pdf_link
    }


@router.get("/{identifier}")
def get_invoice(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("superadmin", "billing", "receptionist")
    ),
):
    # ── Fetch from DB ──
    invoice = (
        db.query(HospitalInvoice)
        .filter(
            (HospitalInvoice.invoice_number == identifier) |
            (HospitalInvoice.appointment_id == identifier)
        )
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = invoice.items
    payments = invoice.payments

    # ── Fresh QR ──
    invoice_url = f"{settings.BASE_URL}/invoice/{invoice.invoice_number}"
    qr = qrcode.make(invoice_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_data_uri = (
            "data:image/png;base64,"
            + base64.b64encode(buffer.getvalue()).decode()
    )

    # ── Re-render HTML ──
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("invoice.html")
    # logo_path = pathlib.Path("app/static/logo.png").resolve().as_uri()
    logo_path = pathlib.Path("C:/Users/SecurXperts/Downloads/logo.png").resolve().as_uri()

    html = template.render(
        invoice=invoice,
        lab={
            "name": "CARE HOSPITAL",
            "phone": "9876543210",
            "email": "care@hospital.com",
            "address": "Madhapur, Hyderabad"
        },
        patient={
            "name": invoice.patient_name,
            "gender": invoice.patient_gender,
            "dob": invoice.patient_dob
        },
        lines=[
            {
                "desc": i.description,
                "qty": i.qty,
                "unit_price": i.unit_price,
                "line_total": i.line_total
            }
            for i in items
        ],
        payments=[
            {
                "amount": p.amount,
                "method": p.method,
                "ref": p.ref,
                "date": p.date
            }
            for p in payments
        ],
        qr_data_uri=qr_data_uri,
        hospital_logo=logo_path
    )

    # ── Generate fresh PDF ──
    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )
    options = {"enable-local-file-access": ""}
    pdf_bytes = pdfkit.from_string(html, False, configuration=config, options=options)

    # ── Upload fresh PDF to S3 ──
    s3_key = f"invoices/{invoice.id}/{invoice.invoice_number}.pdf"
    try:
        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    # ── Redirect directly to PDF ──
    pdf_link = generate_presigned_url(s3_key)
    return {"pdf_url": pdf_link}