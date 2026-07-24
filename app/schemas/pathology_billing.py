from typing import List, Optional
from pydantic import BaseModel, Field


# --- Price Lists ---
class PriceListIn(BaseModel):
    name: str
    currency: str = "INR"
    is_active: bool = True

class PriceListOut(BaseModel):
    id: int
    name: str
    currency: str
    is_active: bool

class PriceForTestIn(BaseModel):
    test_id: int
    price: float

class PriceForPanelIn(BaseModel):
    panel_id: int
    price: float


# --- Invoice ---
class InvoiceCreateIn(BaseModel):
    price_list_id: int
    discount_pct: float = 0.0
    tax_pct: float = 0.0

class InvoiceLineOut(BaseModel):
    id: int
    item_type: str
    ref_id: int
    description: str
    qty: int
    unit_price: float
    line_total: float

class InvoiceOut(BaseModel):
    id: int
    number: str
    order_id: int
    currency: str
    subtotal: float
    discount_pct: float
    discount_value: float
    tax_pct: float
    tax_value: float
    total: float
    due: float
    lines: List[InvoiceLineOut]


# --- Payments ---
class PaymentIn(BaseModel):
    amount: float
    method: str = Field(pattern="^(cash|card|upi|online)$")
    txn_ref: Optional[str] = None
    note: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    amount: float
    method: str
    txn_ref: Optional[str]
    note: Optional[str]
