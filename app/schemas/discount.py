from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.discounts import DiscountType



class ApplyMembershipDiscount(BaseModel):
    phone_number: str
    bill_amount: float


class ApplyDoctorReferralDiscount(BaseModel):
    bill_amount: float
    doctor_name: str
    doctor_reg_no: str
    department: str
    prescription_uploaded: bool


class ApplyPromoCode(BaseModel):
    code: str
    bill_amount: float


class DiscountResponse(BaseModel):
    original_amount: float
    discount_applied: float
    final_amount: float
    message: str

class DiscountAuditCreate(BaseModel):
    bill_id: int
    customer_id: int
    hospital_id: int
    branch_id: int
    discount_type: DiscountType
    discount_value: float
    discount_date: Optional[datetime] = None
    reference_info: Optional[str] = None


# class DiscountAuditResponse(DiscountAuditCreate):
#     id: int
#     pharmacist_id: int
#     applied_by: int
#     created_at: datetime

class DiscountAuditResponse(BaseModel):
    id: int
    bill_no: int
    discount_type: DiscountType
    discount_value: float
    discount_date: datetime
    pharmacist_id: int
    applied_by: int

    model_config = ConfigDict(from_attributes=True)

    # model_config = ConfigDict(from_attributes=True)