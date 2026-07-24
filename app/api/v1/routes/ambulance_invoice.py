from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from datetime import datetime
import os
from dotenv import load_dotenv
import pdfkit
import base64
import mimetypes
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.models.ambulance_invoice import AmbulanceInvoice
from app.models.auth import User
from app.models.blood_bank import UserRole
from app.schemas.ambulance_invoice import AmbulanceInvoiceCreate
from app.core.security import get_db, require_roles

load_dotenv()

router = APIRouter(prefix="/amb-invoice", tags=["Ambulance-Invoice"])

templates = Jinja2Templates(directory="app/templates")

# ─────────────────────────────────────────────
# wkhtmltopdf config
# # ─────────────────────────────────────────────
# config = pdfkit.configuration(
#     wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
# )

# ─────────────────────────────────────────────
# S3 config
# ─────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION            = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME        = os.getenv("AWS_BUCKET_NAME")
S3_FOLDER             = os.getenv("S3_FOLDER", "invoices")

# print("=== S3 CONFIG ===")
# print(f"BUCKET : {repr(S3_BUCKET_NAME)}")
# print(f"REGION : {repr(AWS_REGION)}")
# print(f"KEY ID : {repr(AWS_ACCESS_KEY_ID)}")
# print("=================")

s3_client = boto3.client(
    "s3",
    aws_access_key_id     = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name           = AWS_REGION,
)


# ─────────────────────────────────────────────
# Presigned URL — unique token, expires 1 hour
# ─────────────────────────────────────────────
def generate_presigned_url(s3_key: str) -> str:
    """
    Generates a unique presigned URL every call.
    URL format:
    https://<bucket>.s3.<region>.amazonaws.com/<folder>/<id>/<file>.pdf
        ?AWSAccessKeyId=...&Signature=...&Expires=...
    Expires in 1 hour.
    """
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key"   : s3_key,
        },
        ExpiresIn=3600  # 1 hour
    )


# ─────────────────────────────────────────────
# image → base64
# ─────────────────────────────────────────────
def image_to_base64(path: str) -> str:
    THIS_FILE    = os.path.abspath(__file__)
    ROUTER_DIR   = os.path.dirname(THIS_FILE)
    APP_DIR      = os.path.dirname(ROUTER_DIR)
    PROJECT_ROOT = os.path.dirname(APP_DIR)

    candidates = [
        path,
        os.path.join(PROJECT_ROOT, path),
        os.path.join(APP_DIR,      path),
        os.path.join(ROUTER_DIR,   path),
        os.path.abspath(path),
    ]

    abs_path = None
    for c in candidates:
        if os.path.exists(c):
            abs_path = os.path.abspath(c)
            break

    if abs_path is None:
        print(f" Image not found: {path}")
        return ""

    mime_type, _ = mimetypes.guess_type(abs_path)
    if not mime_type:
        mime_type = "image/png"

    try:
        with open(abs_path, "rb") as f:
            raw = f.read()
        if len(raw) == 0:
            return ""
        encoded  = base64.b64encode(raw).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        print(f" Read error: {abs_path} → {e}")
        return ""


# ─────────────────────────────────────────────
# Indian currency formatting  →  ₹1,500.00
# ─────────────────────────────────────────────
def fmt(value: float) -> str:
    return "{:,.2f}".format(value)


# ─────────────────────────────────────────────
# CREATE INVOICE + PDF
# ─────────────────────────────────────────────
@router.post("/create-amb")
def create_ambulance_invoice(
    request: Request,
    data: AmbulanceInvoiceCreate,
    db: Session = Depends(get_db),
        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    c = data.charges

    # ── Calculations ──────────────────────────
    base_fare_total = c.base_fare_qty  * c.base_fare_unit
    distance_total  = c.distance_qty   * c.distance_unit
    waiting_total   = c.waiting_qty    * c.waiting_unit
    oxygen_total    = c.oxygen_qty     * c.oxygen_unit
    emergency_total = c.emergency_qty  * c.emergency_unit
    night_total     = c.night_qty      * c.night_unit

    subtotal    = base_fare_total + distance_total + waiting_total + oxygen_total + emergency_total + night_total
    tax_amount  = round(subtotal * (data.tax_percent / 100), 2)
    grand_total = round(subtotal + tax_amount - data.discount_amount, 2)

    # ── Step 1: Save invoice to DB ─────────────
    invoice = AmbulanceInvoice(
        patient_name    = data.patient_name,
        patient_age     = data.patient_age,
        patient_gender  = data.patient_gender,
        patient_contact = data.patient_contact,

        booking_person  = data.booking_person,
        pickup_address  = data.pickup_address,
        drop_address    = data.drop_address,

        ambulance_type  = data.ambulance_type,
        vehicle_number  = data.vehicle_number,
        driver_name     = data.driver_name,

        start_time      = data.start_time,
        end_time        = data.end_time,
        distance        = data.distance,

        subtotal        = subtotal,
        tax_percent     = data.tax_percent,
        tax_amount      = tax_amount,
        discount_amount = data.discount_amount,
        grand_total     = grand_total,

        payment_status  = data.payment.payment_status,
        payment_method  = data.payment.payment_method,
        transaction_id  = data.payment.transaction_id,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # ── Step 2: Generate invoice number ────────
    invoice_number     = f"INV-{1000 + invoice.id}"
    invoice.invoice_id = invoice_number
    db.commit()
    db.refresh(invoice)

    # ── Step 3: Load images ────────────────────
    logo_b64 = image_to_base64("static/logo.png")
    qr_b64   = image_to_base64("static/qr.png")

    # ── Step 4: Build template context ─────────
    context = {
        "request"      : request,
        "invoice_id"   : invoice_number,
        "trip_id"      : f"TRIP-{invoice.id}",
        "invoice_date" : datetime.now().strftime("%d-%m-%Y"),

        "hospital_name"    : "CityCare Hospital",
        "hospital_tagline" : "24/7 Emergency Services",
        "hospital_address" : "Hyderabad, India",
        "hospital_phone"   : "+91 9876543210",
        "emergency_number" : "108",

        "patient_name"    : data.patient_name,
        "patient_age"     : data.patient_age,
        "patient_gender"  : data.patient_gender,
        "patient_contact" : data.patient_contact,

        "booking_person" : data.booking_person,
        "pickup_address" : data.pickup_address,
        "drop_address"   : data.drop_address,

        "ambulance_type" : data.ambulance_type,
        "vehicle_number" : data.vehicle_number,
        "driver_name"    : data.driver_name,
        "start_time"     : data.start_time.strftime("%I:%M %p"),
        "end_time"       : data.end_time.strftime("%I:%M %p"),
        "distance"       : f"{data.distance} KM",

        "base_fare_qty"   : c.base_fare_qty,
        "base_fare_unit"  : fmt(c.base_fare_unit),
        "base_fare_total" : fmt(base_fare_total),

        "distance_qty"    : f"{c.distance_qty} KM",
        "distance_unit"   : fmt(c.distance_unit),
        "distance_total"  : fmt(distance_total),

        "waiting_qty"     : f"{c.waiting_qty} mins",
        "waiting_unit"    : fmt(c.waiting_unit),
        "waiting_total"   : fmt(waiting_total),

        "oxygen_qty"      : c.oxygen_qty,
        "oxygen_unit"     : fmt(c.oxygen_unit),
        "oxygen_total"    : fmt(oxygen_total),

        "emergency_qty"   : c.emergency_qty,
        "emergency_unit"  : fmt(c.emergency_unit),
        "emergency_total" : fmt(emergency_total),

        "night_qty"       : c.night_qty,
        "night_unit"      : fmt(c.night_unit),
        "night_total"     : fmt(night_total),

        "subtotal"        : fmt(subtotal),
        "tax_percent"     : fmt(data.tax_percent),
        "tax_amount"      : fmt(tax_amount),
        "discount_amount" : fmt(data.discount_amount),
        "grand_total"     : fmt(grand_total),

        "payment_status"  : data.payment.payment_status,
        "payment_method"  : data.payment.payment_method,
        "transaction_id"  : data.payment.transaction_id,

        "year"        : datetime.now().year,
        "logo_url"    : logo_b64,
        "qr_code_url" : qr_b64,
    }

    # ── Step 5: Render HTML ────────────────────
    template_obj = templates.get_template("ambulance_invoice.html")
    html_content = template_obj.render(context)

    # ── Step 6: Generate PDF bytes ─────────────
    options = {
        "page-size"              : "A4",
        "encoding"               : "UTF-8",
        "margin-top"             : "10mm",
        "margin-bottom"          : "10mm",
        "margin-left"            : "12mm",
        "margin-right"           : "12mm",
        "dpi"                    : "300",
        "zoom"                   : "1.0",
        "disable-smart-shrinking": "",
        "print-media-type"       : "",
        "no-outline"             : "",
        "quiet"                  : "",
    }

    try:
        pdf_bytes = pdfkit.from_string(
            html_content,
            False,
            configuration=config,
            options=options,
        )
        print(f" PDF generated: {len(pdf_bytes)} bytes")
    except Exception as e:
        print(f" PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    # ── Step 7: Upload to S3 ───────────────────
    # Key format: invoices/<invoice_id>/<invoice_number>.pdf
    # e.g.      : invoices/10/INV-1010.pdf
    s3_key = f"{S3_FOLDER}/{invoice.id}/{invoice_number}.pdf"

    try:
        s3_client.put_object(
            Bucket      = S3_BUCKET_NAME,
            Key         = s3_key,
            Body        = pdf_bytes,
            ContentType = "application/pdf",
        )
        print(f" Uploaded to S3: {s3_key}")
    except (BotoCoreError, ClientError) as e:
        print(f" S3 upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    # ── Step 8: Save s3_key to DB ──────────────
    invoice.file_key = s3_key
    db.commit()
    db.refresh(invoice)
    print(f" pdf_key saved to DB: {invoice.file_key}")

    # ── Step 9: Generate presigned URL ─────────
    pdf_link = generate_presigned_url(s3_key)

    return {
        "success"    : True,
        "invoice_id" : invoice_number,
        "pdf_link"   : pdf_link,
    }


# ─────────────────────────────────────────────
# GET INVOICE — fresh presigned URL every call
# ─────────────────────────────────────────────
@router.get("/{invoice_id}")
def get_amb_invoice(invoice_id: str, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    try:
        numeric_id = int(invoice_id.split("-")[1]) - 1000
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid invoice ID. Expected INV-XXXX")

    invoice = db.query(AmbulanceInvoice).filter(AmbulanceInvoice.id == numeric_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Generate fresh presigned URL — unique token, expires in 1 hour
    pdf_link = generate_presigned_url(invoice.file_key) if invoice.file_key else None

    return {
        "invoice_id"   : invoice_id,
        "patient_name" : invoice.patient_name,
        "grand_total"  : fmt(invoice.grand_total),
        "pdf_link"     : pdf_link,   # fresh unique URL every GET
    }