from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Date, DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
from app.models.people import Patient


class DiscountType(enum.Enum):
    MEMBERSHIP = "MEMBERSHIP"
    DOCTOR_REFERRAL = "DOCTOR_REFERRAL"
    SEASONAL = "SEASONAL"
    PROMO_CODE = "PROMO_CODE"


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True)
    member_id = Column(String(50), unique=True, index=True)
    phone_number = Column(String(15), index=True)
    discount_percent = Column(Float)  # 5–15%
    valid_from = Column(Date)
    valid_to = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class DoctorReferral(Base):
    __tablename__ = "doctor_referrals"

    id = Column(Integer, primary_key=True)
    doctor_name = Column(String(100))
    doctor_reg_no = Column(String(50))
    department = Column(String(100))
    discount_percent = Column(Float, default=5)
    hospital_policy_allowed = Column(Boolean, default=True)


class SeasonalDiscount(Base):
    __tablename__ = "seasonal_discounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))  # Diwali, New Year
    discount_percent = Column(Float)
    valid_from = Column(Date)
    valid_to = Column(Date)
    otc_only = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, index=True)
    discount_percent = Column(Float, nullable=True)
    flat_amount = Column(Float, nullable=True)
    min_bill_value = Column(Float, default=0)
    valid_from = Column(Date)
    valid_to = Column(Date)
    max_usage_per_user = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)


class DiscountAudit(Base):
    __tablename__ = "discount_audit"

    id = Column(Integer, primary_key=True)
    bill_no = Column(String(50))
    discount_type = Column(Enum(DiscountType))
    discount_value = Column(Float)
    pharmacist_id = Column(Integer, ForeignKey("users.id"))
    applied_by = Column(Integer, ForeignKey("users.id"))
    reference_info = Column(String(255))  # doctor name / promo code
    hospital_id = Column(Integer,ForeignKey("hospitals.id"),nullable=False,index=True)
    branch_id = Column(Integer,ForeignKey("branches.id"),nullable=False,index=True)
    discount_date = Column(DateTime,default=datetime.utcnow,nullable=False)
    customer_id = Column(Integer, nullable=False, index=True)

    hospital = relationship("Hospital")
    branch = relationship("Branch")