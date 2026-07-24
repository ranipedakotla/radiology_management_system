from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, date
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str  # pharmacist | manager | accounting
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str

class ShiftLogBase(BaseModel):
    shift_type: str  # DAY / EVENING / NIGHT
    login_time: datetime


class ShiftLogCreate(ShiftLogBase):
    user_id: int


class ShiftLogUpdate(BaseModel):
    logout_time: Optional[datetime] = None
    total_sales: Optional[int] = 0


class ShiftLogResponse(ShiftLogBase):
    id: int
    user_id: int
    logout_time: Optional[datetime]
    total_sales: int

class BillingSummaryBase(BaseModel):
    bill_date: date
    cash_amount: float = 0
    upi_amount: float = 0
    card_amount: float = 0
    appointment_id: int
    # total_amount: float


class BillingSummaryCreate(BillingSummaryBase):
    shift_id: int


class BillingSummaryResponse(BillingSummaryBase):
    id: int
    shift_id: int

class BillingSummaryUpdate(BaseModel):
    bill_date: Optional[date] = None
    cash_amount: Optional[float] = None
    upi_amount: Optional[float] = None
    card_amount: Optional[float] = None
    shift_id: Optional[int] = None

#
# class DiscountAuditBase(BaseModel):
#     bill_no: str
#     discount_type: str  # MEMBERSHIP / SEASONAL / REFERRAL
#     discount_value: float
#     discount_date: date
#
#
# class DiscountAuditCreate(DiscountAuditBase):
#     pharmacist_id: int
#
#
# class DiscountAuditResponse(DiscountAuditBase):
#     id: int
#     pharmacist_id: int

class PayrollBase(BaseModel):
    base_salary: float = 0
    shift_allowance: float = 0
    night_allowance: float = 0
    overtime_pay: float = 0
    incentive: float = 0
    total_salary: float


class PayrollCreate(PayrollBase):
    user_id: int


class PayrollResponse(PayrollBase):
    id: int
    user_id: int
    #
    # class Config:
    #     from_attributes = True
model_config = ConfigDict(from_attributes=True)

