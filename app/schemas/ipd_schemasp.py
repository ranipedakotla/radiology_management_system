from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import re


class MedicineItem(BaseModel):
    medicine_id: int = Field(..., gt=0)
    medicine_name: str = Field(..., min_length=1)
    batch_no: str = Field(..., min_length=1)
    expiry_date: datetime
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    model_config = ConfigDict(from_attributes=True)


class CashDenomination(BaseModel):
    denomination: float = Field(..., gt=0)  # 10, 20, 50, 100, 200, 500
    count: int = Field(..., ge=0)


class IPDSupplyRequest(BaseModel):
    patient_uhid: str = Field(..., min_length=1)
    ward_id: str = Field(..., min_length=1)  # "GEN", "ICU"
    doctor_order_ref: str = Field(..., min_length=1)
    medicines: List[MedicineItem] = Field(..., min_items=1)
    total_amount: float = Field(..., gt=0)

    #payments + NOC
    noc_number: Optional[str] = None
    payment_mode: str = Field(..., pattern="^(cash|card)$")

    #cash payment fields
    cash_denominations: Optional[List[CashDenomination]] = None

    #card payment fields
    card_number: Optional[str] = Field(None, pattern=r'^\d{4}\s?\d{4}\s?\d{4}\s?\d{4}?$|^\d{13,19}$')
    card_expiry: Optional[str] = Field(None, pattern=r'^(0[1-9]|1[0-2])/(?:0[1-9]|[1-9][0-9])?$')
    card_cvv: Optional[str] = Field(None, pattern=r'^\d{3,4}$')
    card_txn_ref: Optional[str] = Field(None, min_length=1)


class IPDSupplyResponse(BaseModel):
    success: bool
    issue_ref: str
    message: str
    ward_supply: dict
    payment_mode: str
    noc_number: Optional[str] = None


class IPDReturnRequest(BaseModel):
    issue_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    return_items: List[MedicineItem] = Field(..., min_items=1)

    #refund payments + NOC
    noc_number: Optional[str] = None
    refund_mode: str = "cash"
    refund_cash_denominations: Optional[List[CashDenomination]] = Field(None, min_items=1)
    refund_card_txn_ref: Optional[str] = None


class IPDReturnResponse(BaseModel):
    success: bool
    return_ref: str
    message: str
    reduced_wastage: bool
    billing_adjusted: bool
    refund_mode: str
    refund_amount: float
    noc_number: Optional[str] = None

class WardIssueOut(BaseModel):
    issue_ref: str
    patient_uhid: str
    ward_id: str

    hospital_id: int
    branch_id: int

    total_amount: float
    issued_at: datetime
    status: str
    payment_mode: str
    noc_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WardOut(BaseModel):
    id: int
    hospital_id: int
    branch_id: int
    code: str
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


