import enum
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy import Enum as SqlEnum
from app.db.base import Base


# ================== ENUM ==================

class PaymentMode(str, enum.Enum):
    CASH = "CASH"
    CASHLESS = "CASHLESS"


# ================== 🧪 RESOURCE USAGE ==================

class ResourceUsage(Base):
    __tablename__ = "resource_usage"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(Integer, ForeignKey("emergency_requests.id"))

    # Oxygen
    oxygen_start_time = Column(DateTime)
    oxygen_end_time = Column(DateTime)

    # Ventilator
    ventilator_minutes = Column(Integer)

    # Devices
    ecg_used = Column(Boolean, default=False)
    suction_used = Column(Boolean, default=False)
    defibrillator_used = Column(Boolean, default=False)

    # Consumables
    emergency_medicines_qty = Column(Integer)
    iv_fluids_qty = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())


# ================== 💰 BILLING ==================

class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(Integer, ForeignKey("emergency_requests.id"))

    base_charge = Column(Float)
    distance_km = Column(Float)
    distance_charge = Column(Float)

    oxygen_charge = Column(Float)
    ventilator_charge = Column(Float)
    device_charge = Column(Float)

    waiting_charge = Column(Float)
    night_charge = Column(Float)

    gst_amount = Column(Float)
    total_amount = Column(Float)

    created_at = Column(DateTime, server_default=func.now())


# ================== 💳 INSURANCE / PAYMENT ==================

class Insurance(Base):
    __tablename__ = "insurance_payments"

    id = Column(Integer, primary_key=True, index=True)

    billing_id = Column(Integer, ForeignKey("billings.id"))

    payment_mode = Column(SqlEnum(PaymentMode))

    insurance_covered_amount = Column(Float)   # insurance pays
    patient_payable_amount = Column(Float)     # patient pays

    created_at = Column(DateTime, server_default=func.now())