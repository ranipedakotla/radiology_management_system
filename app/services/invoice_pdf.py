import base64, io, secrets
from datetime import datetime
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.settings import settings
from app.models.billing import PathologyInvoice, Invoice
from app.models.pathology_orders import LabOrder
from app.services.reporting import html_to_pdf_bytes, upload_pdf_and_presign, _qr_data_uri  # reuse

env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "xml"])
)

def _collect_invoice_context(db: Session, invoice_id: int) -> dict[str, Any]:
    inv: PathologyInvoice | None = (
        db.query(PathologyInvoice)
          .options(
              selectinload(PathologyInvoice.lines),
              selectinload(PathologyInvoice.payments),
          )
          .filter(PathologyInvoice.id == invoice_id)
          .one_or_none()
    )
    if not inv:
        raise ValueError("Invoice not found")

    order: LabOrder | None = db.get(LabOrder, inv.order_id)
    patient = order.patient if order else None

    paid = round(sum(p.amount for p in inv.payments), 2) if inv.payments else 0.0

    ctx = {
        "lab": {
            "name": "Vaidhya Narayan",
            "address": "Madhapur 100feet Road",
            "phone": "0000-000000",
            "email": "VaidhyaNarayan@lab.test",
        },
        "invoice": {
            "number": inv.number,
            "created_at": inv.created_at.strftime("%d/%m/%Y %H:%M"),
            "currency": inv.currency,
            "subtotal": f"{inv.subtotal:.2f}",
            "discount_pct": inv.discount_pct,
            "discount_value": f"{inv.discount_value:.2f}",
            "tax_pct": inv.tax_pct,
            "tax_value": f"{inv.tax_value:.2f}",
            "total": f"{inv.total:.2f}",
            "paid": f"{paid:.2f}",
            "due": f"{inv.due:.2f}",
        },
        "order": {
            "order_no": order.order_no if order else "",
        },
        "patient": {
            "name": f"{patient.first_name} {patient.last_name or ''}".strip() if patient else "",
            "sex": patient.sex if patient else "",
            "dob": patient.dob.strftime("%d/%m/%Y") if patient and patient.dob else "",
            "code": patient.code if patient else "",
        },
        "lines": [
            {
                "desc": l.description,
                "qty": l.qty,
                "unit_price": f"{l.unit_price:.2f}",
                "line_total": f"{l.line_total:.2f}",
            } for l in inv.lines
        ],
        "payments": [
            {
                "amount": f"{p.amount:.2f}",
                "method": p.method.upper(),
                "ref": p.txn_ref or "",
                "date": p.paid_at.strftime("%d/%m/%Y %H:%M")
            } for p in sorted(inv.payments, key=lambda x: x.paid_at)
        ]
    }
    return ctx

def render_invoice_html(db: Session, invoice_id: int, verify_url: str) -> str:
    ctx = _collect_invoice_context(db, invoice_id)
    ctx["verify_url"] = verify_url
    ctx["qr_data_uri"] = _qr_data_uri(verify_url)
    template = env.get_template("pathology_invoice.html")
    return template.render(**ctx)

def generate_and_store_invoice_pdf(db: Session, invoice_id: int) -> Invoice:
    token = secrets.token_urlsafe(16)
    verify_url = f"{settings.PUBLIC_BASE_URL}/billing/invoices/verify/{token}"

    html = render_invoice_html(db, invoice_id, verify_url)
    pdf_bytes = html_to_pdf_bytes(html)

    inv: Invoice = db.get(Invoice, invoice_id)
    key = f"{settings.S3_INVOICE_PREFIX}/{inv.number}.pdf"
    presigned = upload_pdf_and_presign(pdf_bytes, key)

    inv.s3_key = key
    inv.pdf_url = presigned
    inv.qr_code_token = token
    db.commit(); db.refresh(inv)
    return inv
