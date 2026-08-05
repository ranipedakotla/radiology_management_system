from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# -----------------------------
# Patient
# -----------------------------
class InvoicePatientBase(BaseModel):
    name: str
    op_ip_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None


class InvoicePatientCreate(InvoicePatientBase):
    pass


class InvoicePatientResponse(InvoicePatientBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Invoice Item
# -----------------------------
class InvoiceItemBase(BaseModel):
    name: str
    category: Optional[str] = None
    qty: int = 1
    price: float
    discount: float = 0.0
    amount: float


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Insurance
# -----------------------------
class InsuranceDetailBase(BaseModel):
    status: Optional[str] = None
    provider: Optional[str] = None
    policy_no: Optional[str] = None
    approval_no: Optional[str] = None
    coverage_split: Optional[str] = None


class InsuranceDetailCreate(InsuranceDetailBase):
    pass


class InsuranceDetailResponse(InsuranceDetailBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Payment
# -----------------------------
class PaymentDetailBase(BaseModel):
    status: Optional[str] = None
    mode: Optional[str] = None
    transaction_id: Optional[str] = None
    collected_by: Optional[str] = None


class PaymentDetailCreate(PaymentDetailBase):
    pass


class PaymentDetailResponse(PaymentDetailBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Billing Summary
# -----------------------------
class BillingSummaryBase(BaseModel):
    subtotal: float
    total_discount: float = 0.0
    taxable_amount: float
    gst: float = 0.0
    grand_total: float
    amount_paid: float = 0.0
    balance_amount: float = 0.0


class BillingSummaryCreate(BillingSummaryBase):
    pass


class BillingSummaryResponse(BillingSummaryBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------
# Invoice
# -----------------------------
class InvoiceBase(BaseModel):
    invoice_no: str
    date: Optional[str] = None
    time: Optional[str] = None
    bill_type: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    generated_by: Optional[str] = None
    signatory_name: Optional[str] = None
    patient_id: int


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]
    insurance: Optional[InsuranceDetailCreate] = None
    payment: Optional[PaymentDetailCreate] = None
    billing: BillingSummaryCreate


class InvoiceResponse(InvoiceBase):
    id: int
    generated_on: datetime

    patient: InvoicePatientResponse
    items: List[InvoiceItemResponse]
    insurance: Optional[InsuranceDetailResponse]
    payment: Optional[PaymentDetailResponse]
    billing: Optional[BillingSummaryResponse]

    class Config:
        from_attributes = True