from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, date

class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role:str
    hospital_id: int
    current_branch_id: int

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# class ShiftOperation(BaseModel):
#     operation: str = Field(
#         ...,
#         description="create_A|create_B|create_C|create_D|update_{id}|delete_{id}|assign_user_{user_id}_shift_{shift_id}_date_{YYYY-MM-DD}",
#     )
#     name: Optional[str] = None
#     start_time: Optional[str] = None
#     end_time: Optional[str] = None
#     user_id: Optional[int] = None
#     shift_id: Optional[int] = None
#     assigned_date: Optional[str] = None
#
# class ShiftResponse(BaseModel):
#     id: int
#     name: str
#     start_time: str
#     end_time: str
#     is_active: bool
#     model_config = ConfigDict(from_attributes=True)
#
# class ShiftStart(BaseModel):
#     shift_name: str
#
# class ShiftOut(BaseModel):
#     id: int
#     pharmacist_id: int
#     shift_id: int
#     start_time: datetime
#     end_time: Optional[datetime]
#     sales_count: int
#     sales_amount: float
#     model_config = ConfigDict(from_attributes=True)

class SaleItemCreate(BaseModel):
    medicine_id: int
    quantity: int
    unit_price: float

class DiscountInfo(BaseModel):
    type: str
    mode: str
    value: float

class SaleCreate(BaseModel):
    patient_type: str
    patient_id: Optional[int] = None
    items: List[SaleItemCreate]
    discount: Optional[DiscountInfo] = None
    payment_mode: str

class SaleOut(BaseModel):
    id: int
    hospital_id: int
    branch_id: int
    pharmacist_id: int
    total_amount: float
    discount_amount: float
    net_amount: float
    payment_mode: str

    model_config = ConfigDict(from_attributes=True)

class DispenseRequest(BaseModel):
    medicine_id: int
    quantity: int
    patient_id: Optional[int] = None
    is_ipd: bool = False

class PurchaseRequestCreate(BaseModel):
    medicine_id: int
    quantity: int

class PurchaseRequestOut(BaseModel):
    id: int
    medicine_id: int
    quantity: int
    status: str
    model_config = ConfigDict(from_attributes=True)

class ApprovalDecision(BaseModel):
    approve: bool
    note: Optional[str] = None

class ApprovalRequestOut(BaseModel):
    id: int
    medicine_id: int
    quantity: int
    status: str
    model_config = ConfigDict(from_attributes=True)



class StockStatusOut(BaseModel):
    id: int
    item_name: str
    stock: int
    status: str  #CRITICAL, LOW, FULL
    color: str #red, orange, green
    min_stock: int
    threshold: str  #1-sheet, medium, full
    model_config = ConfigDict(from_attributes=True)


class DispenseResponse(BaseModel):
    status: str  #"DISPENSED" or "PENDING_ADMIN_APPROVAL"
    request_id: Optional[int] = None
    new_stock: Optional[int] = None

class PrescriptionUploadOut(BaseModel):
    id: int
    filename: str
    file_path: str
    hospital_id: int
    branch_id: int
    patient_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class ApprovalRequestFullOut(ApprovalRequestOut):
    pharmacist_id: int
    patient_id: Optional[int] = None
    pharmacist_name: str
    medicine_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# class ApprovalDecisionOut(BaseModel):
#     request_id: int
#     approved: bool
#     note: Optional[str] = None
#     processed_by: str
#     processed_at: datetime

class ApprovalDecisionOut(BaseModel):
    approved: bool
    processed_by: int
    processed_at: datetime

# class ShiftOperationResponse(BaseModel):
#     success: bool
#     message: str
#     shift_id: Optional[int] = None
#     affected_users: Optional[List[int]] = None
#
class AssignShift(BaseModel):
    user_id:int
    shift_id:int
    assigned_date:date

class PharmacistProfileOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str

# class ShiftCreate(BaseModel):
#         name: str
#         start_time: str
#         end_time: str
#
# class ShiftAssign(BaseModel):
#         user_id: int
#         shift_id: int
#         assigned_date: date


class ShiftCreate(BaseModel):
    name: str
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"


class ShiftResponse(BaseModel):
    id: int
    name: str
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class ShiftOperationResponse(BaseModel):
    success: bool
    message: str
    shift_id: Optional[int] = None
    affected_users: Optional[List[int]] = None


class ShiftAssign(BaseModel):
    user_id: int
    shift_id: int
    assigned_date: date


class ShiftOut(BaseModel):
    id: int
    hospital_id: int
    branch_id: int
    pharmacist_id: int
    shift_id: int
    start_time: datetime
    end_time: Optional[datetime]
    sales_count: int
    sales_amount: float

    model_config = ConfigDict(from_attributes=True)


class PharmacistProfileOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    model_config = ConfigDict(from_attributes=True)



class ShiftOperation(BaseModel):
    operation: str = Field(
        ...,
        description=(
            "create_A|create_B|create_C|create_D|"
            "update_{id}|delete_{id}|"
            "assign_user_{user_id}_shift_{shift_id}_date_{YYYY-MM-DD}"
        ),
    )
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    user_id: Optional[int] = None
    shift_id: Optional[int] = None
    assigned_date: Optional[str] = None



class ShiftStart(BaseModel):
    shift_name: str

