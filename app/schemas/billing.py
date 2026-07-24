
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

# Keep float to match your current services. If you prefer Decimal later, say the word.

class InvoiceItemIn(BaseModel):
    item_type: str  # consultation|lab|service|medicine
    ref_id: int | None = None
    description: str
    qty: int = 1
    unit_price: float = 0.0

class InvoiceCreateIn(BaseModel):
    patient_id: int | None = None
    patient_uid: str | None = None
    visit_id: int | None = None
    appointment_id: int | None = None
    items: list[InvoiceItemIn] = []

class InvoiceFinalizeIn(BaseModel):
    discount_pct: float | None = None
    discount_amount: float | None = None
    tax_pct: float | None = None

class InvoiceItemOut(BaseModel):
    id: int
    item_type: str
    ref_id: int | None
    description: str
    qty: int
    unit_price: float
    line_total: float
    class Config:
        from_attributes = True

class InvoiceOut(BaseModel):
    id: int
    invoice_no: str | None
    status: str
    patient_id: int
    patient_name: str
    visit_id: int
    appointment_id: int
    sub_total: float
    discount_pct: float | None
    discount_amount: float
    tax_pct: float | None
    tax_amount: float
    grand_total: float
    amount_paid: float
    created_at: datetime
    items: list[InvoiceItemOut] = []
    class Config:
        from_attributes = True

class InvoiceListItem(BaseModel):
    id: int
    invoice_no: str | None
    status: str
    patient_name: str
    grand_total: float
    amount_paid: float
    created_at: datetime
    class Config:
        from_attributes = True

class InvoiceListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InvoiceListItem]

class ReceiptCreateIn(BaseModel):
    amount_received: float = Field(..., gt=0)
    mode: str  # Cash | UPI | Card
    utr_no: str | None = None
    cash_500: int = 0
    cash_200: int = 0
    cash_100: int = 0
    cash_50: int = 0
    cash_20: int = 0
    cash_10: int = 0
    notes: str | None = None

class ReceiptOut(BaseModel):
    id: int
    invoice_id: int
    amount_received: float
    mode: str
    utr_no: str | None
    cash_500: int
    cash_200: int
    cash_100: int
    cash_50: int
    cash_20: int
    cash_10: int
    cash_total: float
    notes: str | None
    received_at: datetime
    class Config:
        from_attributes = True
