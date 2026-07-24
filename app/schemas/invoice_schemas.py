# schemas/invoice_schemas.py

from typing import List
from pydantic import BaseModel, Field


class InvoiceItemCreate(BaseModel):
    description: str = None
    qty: int = None
    unit_price: float = None


class InvoicePaymentCreate(BaseModel):
    amount: float = None
    method: str = None
    ref: str = None
    date: str = None


class InvoiceCreate(BaseModel):
    # Remove 'number' field — auto generated now
    appointment_id: int
    currency: str = None

    discount_pct: float = 0
    discount_reason: str = None  # ← new
    tax_pct: float = 0
    paid: float = 0

    referral_name: str = None  # ← new
    referral_amount: float = 0  # ← new

    patient_name: str = None
    patient_gender: str = None
    patient_dob: str = None

    items: List[InvoiceItemCreate] = Field(default_factory=list)
    payments: List[InvoicePaymentCreate] = Field(default_factory=list)
