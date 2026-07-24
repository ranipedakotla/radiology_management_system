# app/schemas/vendor.py
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator, Field

class MedicineBase(BaseModel):
    name: str
    strength: str
    dosage_form: str
    expire_date: Optional[date] = None
    quantity: Optional[int] = None
    Description: Optional[str] = None
    Drug_formula: Optional[str] = None
    company: Optional[str] = None

class MedicineCreate(MedicineBase):
    pass

class MedicineOut(MedicineBase):
    id: int

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    expire_date: Optional[date] = None
    quantity: Optional[int] = None
    Description: Optional[str] = None
    Drug_formula: Optional[str] = None
    company: Optional[str] = None
class Config:
        from_attributes = True
class VendorBase(BaseModel):
    name: str
    gst_no: Optional[str] = None
    contact: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    drug_license_number: Optional[str] = None
    vendor_category: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    hospital_id: int
    branch_id: int
    pincode: Optional[str] = None
    products_available: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = "pending"
    is_active: bool = True


class VendorCreate(VendorBase):
    pass

class VendorPerformance(BaseModel):
    delivery_timeliness: int
    medicine_quality: int
    price_consistency: int
    expiry_risk: int
    payment_history: int

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    gst_no: Optional[str] = None
    contact: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    drug_license_number: Optional[str] = None
    vendor_category: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    hospital_id: int
    branch_id: int
    pincode: Optional[str] = None
    products_available: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

    delivery_timeliness: Optional[float] = None
    medicine_quality: Optional[float] = None
    price_consistency: Optional[float] = None
    expiry_risk: Optional[float] = None
    payment_history: Optional[float] = None



from enum import Enum

class VendorRating(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    BLACKLISTED = "Blacklisted"

# class VendorCreate(BaseModel):
#     name: str
#     contact: Optional[str]
#     email: Optional[str]
#     gst_no: Optional[str] = None
#
#     delivery_timeliness: float = 0
#     medicine_quality: float = 0
#     price_consistency: float = 0
#     expiry_risk: float = 0
#     payment_history: float = 0
class VendorCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    email: Optional[str] = None
    gst_no: Optional[str] = None

    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None

    drug_license_number: Optional[str] = None
    vendor_category: Optional[str] = None

    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

    pincode: Optional[str] = None
    products_available: Optional[str] = None

    delivery_timeliness: int
    medicine_quality: int
    price_consistency: int
    expiry_risk: int
    payment_history: int

# class VendorOut(VendorBase):
#     id: int

class VendorOut(VendorBase, VendorPerformance):
    id: int
    rating: VendorRating

    model_config = ConfigDict(from_attributes=True)


# class VendorOut(BaseModel):
#     id: int
#     name: str
#     email: str
#     status: str
class VendorOut(VendorBase, VendorPerformance):
    id: int
    rating: VendorRating = VendorRating.AVERAGE

    class Config:
        from_attributes = True

VALID_STATUSES = {"pending", "approved", "rejected", "inactive", "active"}


class VendorStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_statuses(cls, value: str):
        value = value.lower().strip()

        if value not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
            )
        return value


class VendorTransactionCreate(BaseModel):
    type: str = Field(..., description="credit or debit")
    amount: float = Field(..., gt=0, description="Transaction amount")
    reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str):
        value = value.lower().strip()

        if value not in ["credit", "debit"]:
            raise ValueError("type must be credit or debit")

        return value


class VendorPaymentBase(BaseModel):
    vendor_id: int
    hospital_id: int
    branch_id: int

    amount: float = Field(..., gt=0, description="Payment amount")
    payment_date: Optional[date] = None

    payment_mode: str = Field(..., description="cash / upi / bank / cheque")
    reference_no: Optional[str] = None
    notes: Optional[str] = None


class VendorPaymentCreate(VendorPaymentBase):
    pass


class VendorPaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    payment_date: Optional[date] = None
    payment_mode: Optional[str] = None
    reference_no: Optional[str] = None
    notes: Optional[str] = None


class VendorPaymentOut(VendorPaymentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)











class VendorReturnItemCreate(BaseModel):
    batch_id: int
    quantity: int
    reason: Optional[str] = None


# =========================================================
# RETURN CREATE
# =========================================================

class VendorReturnCreate(BaseModel):
    vendor_id: int
    grn_id: Optional[int] = None
    reason: Optional[str] = None

    items: List[VendorReturnItemCreate]


# =========================================================
# ITEM OUT
# =========================================================

class VendorReturnItemOut(BaseModel):
    id: int

    batch_id: int
    medicine_id: int

    quantity: int

    reason: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# RETURN OUT
# =========================================================

class VendorReturnOut(BaseModel):
    id: int

    hospital_id: int
    branch_id: int

    vendor_id: int

    grn_id: Optional[int] = None

    return_number: str

    reason: Optional[str] = None

    status: str

    created_at: datetime

    items: List[VendorReturnItemOut]

    model_config = ConfigDict(
        from_attributes=True
    )


