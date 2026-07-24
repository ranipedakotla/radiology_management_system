
from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.models.appointments import PriorityEnum
from enum import Enum

Priority = Literal["Normal", "Emergency"]
# PaymentMode = Literal["Cash", "Card", "Online", "UPI", "pay_at_hospital"]

class PaymentMode(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    ONLINE = "Online"
    UPI = "UPI"
    PAY_AT_HOSPITAL = "pay_at_hospital"

class AppointmentCreate(BaseModel):
    # required IDs
    patient_id: int
    doctor_id: int
    schedule_date: datetime
    cash_denomination: int | None = None
    # optional
    visit_type: str | None = Field(default=None, description="reserved for later")
    shift: str | None = None
    slot_label: str
    # priority: PriorityEnum | None = None
    priority: PriorityEnum = PriorityEnum.LOW
    payment_status: str | None = "pending"
    payment_mode: PaymentMode | None = "Cash"
    phone_number: int
    notes: str | None = None
    doctor_fee: int | None = None
    discount_pct: int | None = 0
    status: str | None = "booked" or "not-booked" or "pending"
    is_video: bool | None = False

    notes: str | None = None
    # age: Optional[str] | None = None
    cash_total: int | None = None
    gender: str
    blood_group: str
    ward_name: str | None = None
    # datetime: str | None = None
    # datetime: Mapped[datetime] = mapped_column()
    # scheduled_for: Mapped[datetime]
    # cash denominations (when payment_mode == Cash)
    cash_500: int | None = 0
    cash_200: int | None = 0
    cash_100: int | None = 0
    cash_50: int | None = 0
    cash_20: int | None = 0
    cash_10: int | None = 0
    cash_5: int | None = 0
    cash_2: int | None = 0
    cash_1: int | None = 0


    # UTR / reference (when payment_mode != Cash)
    utr_no: str | None = None

    # --- NEW ---
    patient_name: str | None = None
    doctor_name: str | None = None
    department: str | None = None
    discount_reason: str | None = None
    referral_name: str | None = None
    referral_amount: int | None = 0          # stored only; does not change amount_payable

class AppointmentOutIDs(BaseModel):
    id: int
    appointment_no: str
    patient_id: int
    doctor_id: int
    schedule_date: datetime
    # status: str
    shift: str | None
    slot_label: str | None
    # datetime:datetime | None = None
    # datetime: Mapped[datetime] = mapped_column()
    # scheduled_for: Mapped[datetime]
    # priority: Priority

    # priority: PriorityEnum
    priority: PriorityEnum = PriorityEnum.LOW
    # payment_Type: PaymentType
    payment_status: str | None = None
    payment_mode: PaymentMode | None = None
    doctor_fee: int | None
    # age: Optional[str]| None = None
    gender: str | None = None
    blood_group: str | None = None
    phone_number:int | None = None
    ward_name: str | None
    discount_pct: int
    is_video: bool
    status: str | None = "booked" or "not-booked" or "pending"
    amount_payable: int
    cash_denomination: int | None = None
    utr_no: str | None = None
    cash_total: int | None = None

    # --- NEW ---
    department: str | None = None
    discount_reason: str | None = None
    referral_name: str | None = None
    referral_amount: int | None = 0
    change_amount: int | None = 0
    doctor_fee: int | None = None
    med_history_file_path: Optional[str] | None = None

    class Config:
        from_attributes = True

class AppointmentOut(BaseModel):
    id: int
    appointment_no: str
    patient_name: str|None
    doctor_name: str
    patient_id: int
    doctor_id: int
    schedule_date: datetime
    shift: str | None
    slot_label: str | None
    priority: str
    payment_mode: str
    phone_number:int | None = None
    # age: str | None
    gender: str
    blood_group: str
    ward_name: str| None
    doctor_fee: int | None
    discount_pct: int | None
    status: str | None = "booked" or "not-booked" or "pending"
    amount_payable: int
    utr_no: str | None = None
    cash_total: int | None = None

    # --- NEW ---
    department: str | None = None
    discount_reason: str | None = None
    referral_name: str | None = None
    referral_amount: int | None = 0
    med_history_file_path: str | None = None

    class Config:
        from_attributes = True

class AppointmentOutage(BaseModel):
    id: int
    appointment_no: str
    patient_name: str|None
    doctor_name: str
    patient_id: int
    doctor_id: int
    schedule_date: datetime
    shift: str | None
    slot_label: str | None
    priority: str
    payment_mode: str
    phone_number:int | None = None
    age: int | None
    gender: str
    blood_group: str
    ward_name: str| None
    doctor_fee: int | None
    discount_pct: int | None
    status: str | None = "booked" or "not-booked" or "pending"
    amount_payable: int
    utr_no: str | None = None
    cash_total: int | None = None

    # --- NEW ---
    department: str | None = None
    discount_reason: str | None = None
    referral_name: str | None = None
    referral_amount: int | None = 0
    med_history_file_path: str | None = None

    class Config:
        from_attributes = True



class AppointmentDetailOut(AppointmentOutage):
    cash_500: int | None = None
    cash_200: int | None = None
    cash_100: int | None = None
    cash_50: int | None = None
    cash_20: int | None = None
    cash_10: int | None = None
    cash_5: int | None = None
    cash_2: int | None = None
    cash_1: int | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    refund_amount: int | None = None
    refund_mode: PaymentMode | None = None
    refund_cash_500: int | None = None
    refund_cash_200: int | None = None
    refund_cash_100: int | None = None
    refund_cash_50: int | None = None
    refund_cash_20: int | None = None
    refund_cash_10: int | None = None
    refund_cash_5: int | None = None
    refund_cash_2: int | None = None
    refund_cash_1: int | None = None
    refund_cash_total: int | None = None
    refund_utr_no: str | None = None

class AppointmentListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AppointmentOut]

class AppointmentCancelIn(BaseModel):
    reason: str
    refund: bool = False
    refund_amount: int | None = None
    refund_mode: PaymentMode | None = None
    refund_cash_500: int | None = 0
    refund_cash_200: int | None = 0
    refund_cash_100: int | None = 0
    refund_cash_50: int | None = 0
    refund_cash_20: int | None = 0
    refund_cash_10: int | None = 0
    refund_cash_5: int | None = 0
    refund_cash_2: int | None = 0
    refund_cash_1: int | None = 0
    refund_utr_no: str | None = None

class AppointmentCancelOut(BaseModel):
    id: int
    status: str
    cancelled_at: datetime | None
    refund_amount: int | None
    refund_mode: PaymentMode | None
    refund_cash_total: int | None = None
    refund_utr_no: str | None = None

from pydantic import BaseModel
from datetime import date, time

class CreateAvailabilityRequest(BaseModel):
    doctor_id: int
    # day_of_week: int
    schedule_date:datetime
    slot_minutes: int
    # for_date: date
    # slot_hours: int | None = None
    max_patients: int | None = None
    start_time: time
    end_time: time
    hospital_id: int
    branch_id: int

class AvailabilitySlotOut(BaseModel):
    start: datetime
    end: datetime
    label: str
    available: bool

AppointmentOut.model_rebuild()
AppointmentDetailOut.model_rebuild()
AppointmentListOut.model_rebuild()