from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from numpy import select
from sqlalchemy.orm import Session
from sqlalchemy import Boolean

from app.core.security import require_roles, get_current_user
from app.core.security import async_get_db

from app.models.pathology_tests import Test, Panel
from app.models.pathology_orders  import LabOrder, LabOrderItem
from app.models.billing import (
    PriceList, PriceListTest, PriceListPanel,
    PathologyInvoice, InvoiceLine, Payment
)
from app.schemas.pathology_billing  import (
    PriceListIn, PriceListOut, PriceForTestIn, PriceForPanelIn,
    InvoiceCreateIn, InvoiceOut, InvoiceLineOut,
    PaymentIn, PaymentOut
)
from fastapi.responses import RedirectResponse, JSONResponse
import boto3
from app.core.settings import settings
from app.services.invoice_pdf import generate_and_store_invoice_pdf
from app.models.billing import Invoice

router = APIRouter(prefix="/billing", tags=["Billing"])

WriteDep = Depends(require_roles(["super_admin", "admin", "receptionist"]))
ReadDep  = Depends(require_roles(["super_admin", "admin", "receptionist", "technician", "doctor"]))


# ---------- helpers ----------
def _gen_inv_no(n: int) -> str:
    y = datetime.utcnow().strftime("%Y%m")
    return f"INV-{y}-{n:06d}"

def _s3():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

def _invoice_out(inv: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=inv.id, number=inv.number, order_id=inv.order_id, currency=inv.currency,
        subtotal=inv.subtotal, discount_pct=inv.discount_pct, discount_value=inv.discount_value,
        tax_pct=inv.tax_pct, tax_value=inv.tax_value, total=inv.total, due=inv.due,
        lines=[InvoiceLineOut(
            id=l.id, item_type=l.item_type, ref_id=l.ref_id, description=l.description,
            qty=l.qty, unit_price=l.unit_price, line_total=l.line_total
        ) for l in inv.lines]
    )


# ---------- price lists ----------
@router.post("/price-lists", response_model=PriceListOut, dependencies=[WriteDep])
def create_price_list(payload: PriceListIn, db: Session = Depends(async_get_db)):
    if db.query(PriceList).filter(PriceList.name == payload.name).one_or_none():
        raise HTTPException(400, "Price list name already exists")
    p = PriceList(name=payload.name, currency=payload.currency, is_active=payload.is_active)
    db.add(p); db.commit(); db.refresh(p)
    return PriceListOut(id=p.id, name=p.name, currency=p.currency, is_active=p.is_active)

@router.post("/price-lists/{pl_id}/tests", dependencies=[WriteDep])
def add_test_price(pl_id: int, payload: PriceForTestIn, db: Session = Depends(async_get_db)):
    if not db.get(PriceList, pl_id):
        raise HTTPException(404, "Price list not found")
    if not db.get(Test, payload.test_id):
        raise HTTPException(400, "Invalid test_id")
    existing = db.query(PriceListTest).filter(
        PriceListTest.price_list_id == pl_id, PriceListTest.test_id == payload.test_id
    ).one_or_none()
    if existing:
        existing.price = payload.price
    else:
        db.add(PriceListTest(price_list_id=pl_id, test_id=payload.test_id, price=payload.price))
    db.commit()
    return {"ok": True}

@router.post("/price-lists/{pl_id}/panels", dependencies=[WriteDep])
def add_panel_price(pl_id: int, payload: PriceForPanelIn, db: Session = Depends(async_get_db)):
    if not db.get(PriceList, pl_id):
        raise HTTPException(404, "Price list not found")
    if not db.get(Panel, payload.panel_id):
        raise HTTPException(400, "Invalid panel_id")
    existing = db.query(PriceListPanel).filter(
        PriceListPanel.price_list_id == pl_id, PriceListPanel.panel_id == payload.panel_id
    ).one_or_none()
    if existing:
        existing.price = payload.price
    else:
        db.add(PriceListPanel(price_list_id=pl_id, panel_id=payload.panel_id, price=payload.price))
    db.commit()
    return {"ok": True}


# ---------- invoice ----------
@router.post("/{order_id}/invoice", response_model=InvoiceOut, dependencies=[WriteDep])
def create_invoice(order_id: int, payload: InvoiceCreateIn, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    pl = db.get(PriceList, payload.price_list_id)
    if not pl:
        raise HTTPException(404, "Price list not found")

    # prevent duplicate invoice per order (simple rule)
    existing = db.query(Invoice).filter(Invoice.order_id == order_id).one_or_none()
    if existing:
        return _invoice_out(existing)

    inv = Invoice(order_id=order_id, number="", currency=pl.currency,
                  discount_pct=payload.discount_pct, tax_pct=payload.tax_pct,
                  created_by=user.id)
    db.add(inv); db.flush()
    inv.number = _gen_inv_no(inv.id)

    subtotal = 0.0

    for it in o.items:
        # price by TEST (simplest & covers our flow); panel pricing optional
        t = it.test
        row = db.query(PriceListTest).filter(
            PriceListTest.price_list_id == pl.id, PriceListTest.test_id == t.id
        ).one_or_none()
        if not row:
            raise HTTPException(400, f"No price for test {t.code} in price list {pl.name}")
        line_total = float(row.price)
        subtotal += line_total
        db.add(InvoiceLine(
            invoice_id=inv.id, item_type="test", ref_id=t.id, description=t.name,
            qty=1, unit_price=row.price, line_total=line_total
        ))

    inv.subtotal = round(subtotal, 2)
    base = max(inv.subtotal - (inv.subtotal * (payload.discount_pct / 100.0)), 0.0)
    inv.discount_value = round(inv.subtotal - base, 2)
    tax = round(base * (payload.tax_pct / 100.0), 2)
    inv.tax_value = tax
    inv.total = round(base + tax, 2)
    inv.due = inv.total  # will reduce on payments

    db.commit(); db.refresh(inv)
    return _invoice_out(inv)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut, dependencies=[ReadDep])
def get_invoice(invoice_id: int, db: Session = Depends(async_get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return _invoice_out(inv)


# ---------- payments ----------
@router.post("/invoices/{invoice_id}/payments", response_model=PaymentOut, dependencies=[WriteDep])
def add_payment(invoice_id: int, payload: PaymentIn, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    pay = Payment(invoice_id=invoice_id, amount=payload.amount, method=payload.method,
                  txn_ref=payload.txn_ref, note=payload.note, recorded_by=user.id)
    db.add(pay)
    # reduce due
    inv.due = round(max(inv.due - payload.amount, 0.0), 2)
    db.commit(); db.refresh(pay); db.refresh(inv)
    return PaymentOut(id=pay.id, amount=pay.amount, method=pay.method, txn_ref=pay.txn_ref, note=pay.note)




@router.post("/invoices/{invoice_id}/pdf", dependencies=[WriteDep])
def generate_invoice_pdf(invoice_id: int, db: Session = Depends(async_get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv = generate_and_store_invoice_pdf(db, invoice_id)
    return {
        "invoice_id": inv.id,
        "number": inv.number,
        "s3_key": inv.s3_key,
        "pdf_url": inv.pdf_url,
        "verify_url": f"{settings.PUBLIC_BASE_URL}/billing/invoices/verify/{inv.qr_code_token}"
    }



# @router.get("/invoices/verify/{token}")
# def verify_invoice(token: str, db: Session = Depends(async_get_db)):
#     # inv = db.query(Invoice).filter(Invoice.qr_code_token == token).one_or_none()
#     stmt = select(Invoice).where(Invoice.qr_code_token == token)
#     result = await db.execute(stmt)
#     inv = result.scalar_one_or_none()
#     if not inv or not inv.s3_key:
#         raise HTTPException(404, "Invoice not found or unavailable")
#
#     s3 = _s3()
#     url = s3.generate_presigned_url(
#         "get_object",
#         Params={"Bucket": settings.S3_BUCKET, "Key": inv.s3_key},
#         ExpiresIn=settings.REPORT_URL_EXPIRES,
#     )
#     return RedirectResponse(url)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/verify/{token}")
async def verify_invoice(
    token: str,
    db: AsyncSession = Depends(async_get_db)
):
    stmt = select(Invoice).where(Invoice.qr_code_token == token)

    result = await db.execute(stmt)
    inv = result.scalar_one_or_none()

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return inv