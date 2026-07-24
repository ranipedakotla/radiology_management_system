import base64
import io
import secrets
from typing import Any
import boto3
import qrcode
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.models.people import Patient, Doctor
from sqlalchemy.orm import Session
from app.core.settings import settings
from sqlalchemy.orm import selectinload, joinedload
from app.models.pathology_orders  import LabOrder, LabOrderItem, Report, ResultValue, Result
from app.models.pathology_tests  import Test, Analyte, Unit, SampleType
from qrcode.image.pil import PilImage
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys, asyncio

# --- Templating (loads from app/templates/) ---
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"])
)

def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def _qr_data_uri(text: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)

    # Generate QR code with white background first
    img: PilImage = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # Replace white with transparent
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > 240 and item[1] > 240 and item[2] > 240:  # white pixel
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append(item)
    img.putdata(new_data)

    # Save as base64 data URI
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _format_range(low, high, unit_symbol: str | None) -> str:
    unit = f" {unit_symbol}" if unit_symbol else ""
    if low is not None and high is not None:
        return f"{low:g} – {high:g}{unit}"
    if low is not None:
        return f"≥ {low:g}{unit}"
    if high is not None:
        return f"≤ {high:g}{unit}"
    return ""


def _collect_report_context(db: Session, order_id: int) -> dict[str, Any]:
    order: LabOrder | None = (
        db.query(LabOrder)
        .options(
            joinedload(LabOrder.patient),
            joinedload(LabOrder.doctor),
            # Items -> Test -> Analytes -> Unit
            selectinload(LabOrder.items)
            .joinedload(LabOrderItem.test)
            .selectinload(Test.analytes)
            .joinedload(Analyte.unit),
            # Items -> Result -> Values
            selectinload(LabOrder.items)
            .joinedload(LabOrderItem.result)
            .selectinload(Result.values),
            # Items -> Sample Type
            selectinload(LabOrder.items).joinedload(LabOrderItem.sample_type),
        )
        .filter(LabOrder.id == order_id)
        .one_or_none()
    )

    if not order:
        raise ValueError("Order not found")
    patient: Patient = order.patient
    doctor: Doctor | None = order.doctor

    # Make view rows per order item / per analyte
    sections = []
    for item in order.items:
        t: Test = item.test
        # map analyte_id -> ResultValue (latest if multiple)
        val_by_analyte: dict[int, ResultValue] = {}
        if item.result:
            for rv in item.result.values:
                val_by_analyte[rv.analyte_id] = rv
        rows = []
        for a in t.analytes:
            unit_symbol = a.unit.symbol if a.unit else None
            rv = val_by_analyte.get(a.id)
            if rv and rv.value_num is not None:
                value = f"{rv.value_num:g}"
            elif rv and rv.value_text:
                value = rv.value_text
            else:
                value = ""
            rr = a.ranges[0] if a.ranges else None
            ref = _format_range(rr.low if rr else None, rr.high if rr else None, unit_symbol)
            rows.append({
                "name": a.name,
                "value": value,
                "unit": unit_symbol or "",
                "flag": rv.flag if rv else "",
                "ref": ref,
                "interp": rv.interpretation if rv else "",  # NEW
                "note": rv.note if rv else "",  # NEW
            })

        sections.append({
            "test_code": t.code,
            "test_name": t.name,
            "rows": rows,
            "specimen": (item.sample_type.name if item.sample_type else t.sample_type.name if getattr(t, "sample_type",
                                                                                                      None) else ""),
            "collected_at": item.sample_collected_at.strftime("%d/%m/%Y %H:%M") if item.sample_collected_at else "",
            "test_interp": (item.result.test_interpretation if item.result else ""),  # NEW
            "test_note": (item.result.test_note if item.result else ""),  # NEW
        })
    # reporting.py  (inside _collect_report_context, after doctor = order.doctor)
    sig_url = ""
    if doctor and doctor.signature_url:
        # cache-bust with updated_at if available
        if getattr(doctor, "signature_updated_at", None):
            sig_url = f"{doctor.signature_url}&t={int(doctor.signature_updated_at.timestamp())}"
        else:
            sig_url = doctor.signature_url

    context = {
        "lab": {
            "name": "Vaidhya Narayan",
            "address": "Madhapur 100feet Road",
            "phone": "0000-000000",
            "email": "VaidhyaNarayan@lab.test",
            "web": "www.securxperts.com"
        },
        "order": {
            "order_no": order.order_no,
            "created_at": order.created_at.strftime("%d/%m/%Y %H:%M"),
            "status": order.status,
        },
        "patient": {
            "name": f"{patient.first_name} {patient.last_name or ''}".strip(),
            "sex": patient.sex,
            "dob": patient.dob.strftime("%d/%m/%Y") if patient.dob else "",
            "code": patient.code or "",
        },
        "doctor": {
            "name": doctor.full_name if doctor else "",
            "reg": doctor.registration_no if doctor else "",
            "sig_url":sig_url,
        },
        "sections": sections,
    }
    return context


def render_report_html(db: Session, order_id: int, verify_url: str) -> str:
    ctx = _collect_report_context(db, order_id)
    ctx["verify_url"] = verify_url
    ctx["qr_data_uri"] = _qr_data_uri(verify_url)
    template = env.get_template("report.html")
    return template.render(**ctx)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def html_to_pdf_bytes(html: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "report.html"
        html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            try:
                page = browser.new_page()
                page.goto(html_path.as_uri(), wait_until="networkidle")
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
                )
                return pdf_bytes
            finally:
                browser.close()




def upload_pdf_and_presign(pdf_bytes: bytes, key: str) -> str:
    s3 = _s3_client()
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ACL="private",
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=settings.REPORT_URL_EXPIRES,
    )
    return url


def generate_and_store_report(db: Session, order_id: int, user_id: int) -> Report:
    # make token & verify URL
    token = secrets.token_urlsafe(16)
    verify_url = f"{settings.PUBLIC_BASE_URL}/reports/verify/{token}"

    html = render_report_html(db, order_id, verify_url)
    pdf_bytes = html_to_pdf_bytes(html)

    # s3 key: reports/ORD-YYYYMM-XXXXXX-vN.pdf
    order: LabOrder = db.get(LabOrder, order_id)


    existing = db.query(Report).filter(Report.order_id == order_id, Report.is_current == True).all()  # noqa
    for r in existing:
        r.is_current = False
    version = (max([r.version for r in existing]) + 1) if existing else 1
    key = f"{settings.S3_REPORT_PREFIX}/{order.order_no}-v{version}.pdf"

    presigned = upload_pdf_and_presign(pdf_bytes, key)

    rep = Report(
        order_id=order_id,
        version=version,
        is_current=True,
        created_by=user_id,
        s3_key=key,
        pdf_url=presigned,      # store last presigned for convenience
        qr_code_token=token,
    )
    db.add(rep)
    order.status = "reported"
    db.commit()
    db.refresh(rep)
    return rep
