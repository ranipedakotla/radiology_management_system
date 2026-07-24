from sqlalchemy import ForeignKey, String, Boolean, Integer, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base
from app.models._mixins import TenantedMixin
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class PaymentType(str, Enum):
        CASH = "cash"
        UPI = "upi"


class PriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"
    Normal = "Normal"

class Appointment(Base, TenantedMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("branch_id", "doctor_id", "schedule_date", name="uq_appt_branch_doctor_time"),
        Index("ix_appt_branch_time", "branch_id", "schedule_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    appointment_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    # TENANCY
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True)

    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)

    # scheduled_for: Mapped[datetime]
    schedule_date: Mapped[datetime] = mapped_column(DateTime)
    # status & notes
    status: Mapped[str] = mapped_column(String(20), default="booked")
    notes: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # datetime :[str]
    # datetime: Mapped[datetime] = mapped_column()

    # UI fields
    shift: Mapped[str | None] = mapped_column(String(20), default=None)
    slot_label: Mapped[str | None] = mapped_column(String(20), default=None)
    # priority: Mapped[str] = mapped_column(String(20), default="Low", "Medium", "High", "Urgent")
    # priority: Literal["Low", "Medium", "High", "Urgent"]
    priority: PriorityEnum
    priority: Mapped[PriorityEnum] = mapped_column(
        SQLEnum(PriorityEnum),
        default=PriorityEnum.LOW
    )
    # payment (booking)
    payment_mode: Mapped[str] = mapped_column(String(20), default="Cash")
    doctor_fee: Mapped[int | None] = mapped_column(Integer, default=None)
    discount_pct: Mapped[int] = mapped_column(Integer, default=0)
    is_video: Mapped[bool] = mapped_column(Boolean, default=False)
    amount_payable: Mapped[int] = mapped_column(Integer, default=0)
    # cash_denomination:Mapped[int]= mapped_column(Integer, default=0)
    # appointment_type: Mapped[str] = mapped_column(String(50))
    # age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(10))
    ward_name: Mapped[str] = mapped_column(String(100))
    blood_group: Mapped[str] = mapped_column(String(5))
    phone_number:Mapped[str] = mapped_column(String(20))

    # cash denominations for booking
    cash_500: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_200: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_100: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_50: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_20: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_10: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_5: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_2: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_1: Mapped[int | None] = mapped_column(Integer, default=0)
    cash_total: Mapped[int | None] = mapped_column(Integer, default=0)

    utr_no: Mapped[str | None] = mapped_column(String(64), default=None)

    # cancellation / refund
    cancelled_at: Mapped[datetime | None]
    cancel_reason: Mapped[str | None] = mapped_column(Text, default=None)
    refund_amount: Mapped[int | None] = mapped_column(Integer, default=None)
    refund_mode: Mapped[str | None] = mapped_column(String(20), default=None)

    refund_cash_500: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_200: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_100: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_50: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_20: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_10: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_5: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_2: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_1: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_cash_total: Mapped[int | None] = mapped_column(Integer, default=0)
    refund_utr_no: Mapped[str | None] = mapped_column(String(64), default=None)

    change_amount: Mapped[int | None] = mapped_column(Integer, default=0)

    # --- NEW snapshot & meta fields ---
    patient_name_snapshot: Mapped[str | None] = mapped_column(String(160), default=None)
    doctor_name_snapshot: Mapped[str | None] = mapped_column(String(160), default=None)
    department: Mapped[str | None] = mapped_column(String(120), default=None)
    discount_reason: Mapped[str | None] = mapped_column(Text, default=None)
    referral_name: Mapped[str | None] = mapped_column(String(120), default=None)
    referral_amount: Mapped[int | None] = mapped_column(Integer, default=0)
    med_history_file_path: Mapped[str | None] = mapped_column(String(300), default=None)
    payment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending"
    )

    # relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    # doctor relationship optional
    invoice = relationship(
        "HospitalInvoice",
        back_populates="appointment",
        uselist=False
    )