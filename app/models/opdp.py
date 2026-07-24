
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# from app.models.medicine import Medicine
from app.db.base import Base
import enum

class PharmacyType(enum.Enum):
    OPD = "OPD"
    IPD = "IPD"
    OUTSIDE = "OUTSIDE"

class MedicineCategory(enum.Enum):
    NORMAL = "NORMAL"
    SCHEDULE_H = "SCHEDULE_H"
    SCHEDULE_H1 = "SCHEDULE_H1"
    SCHEDULE_X = "SCHEDULE_X"
#
# class Medicine(Base):
#     __tablename__ = "medicines"
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100))
#     category = Column(Enum(MedicineCategory))
#     is_restricted = Column(Boolean, default=False)

# class Prescription(Base):
#     __tablename__ = "prescriptions"
#
#     id = Column(Integer, primary_key=True)
#     doctor_name = Column(String(100))
#     doctor_reg_no = Column(String(50))
#     prescription_date = Column(Date)
#     image_url = Column(String(255))

# class PharmacyIssue(Base):
#     __tablename__ = "pharmacy_issues"
#
#     id = Column(Integer, primary_key=True)
#     pharmacy_type = Column(Enum(PharmacyType))
#     medicine_id = Column(ForeignKey("medicines.id"))
#     prescription_id = Column(ForeignKey("prescriptions.id"), nullable=True)
#     patient_name = Column(String(100))
#     patient_id_proof = Column(String(50))
#     quantity = Column(Integer)
#     pharmacist_sign = Column(String(100))
#     issued_at = Column(Date, server_default=func.now())

# class CashFlow(Base):
#     __tablename__ = "cash_flow"
#
#     id = Column(Integer, primary_key=True, index=True)
#     reference_type = Column(String, nullable=False)  # PHARMACY / OPD
#     reference_id = Column(Integer, nullable=False)
#
#     payment_mode = Column(String, nullable=False)  # CASH / UPI
#     amount = Column(Float, nullable=False)
#
#     upi_app = Column(String, nullable=True)  # GPay, PhonePe, Paytm
#     created_by = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#
#     denominations = relationship(
#         "CashDenomination",
#         back_populates="cash_flow",
#         uselist=False
#     )

class CashDenomination(Base):
        __tablename__ = "cash_denominations"

        id = Column(Integer, primary_key=True, index=True)
        cash_flow_id = Column(Integer, ForeignKey("cash_flow.id"))

        note_2000 = Column(Integer, default=0)
        note_500 = Column(Integer, default=0)
        note_200 = Column(Integer, default=0)
        note_100 = Column(Integer, default=0)
        note_50 = Column(Integer, default=0)
        note_20 = Column(Integer, default=0)
        note_10 = Column(Integer, default=0)
        coins = Column(Float, default=0)

        total_cash = Column(Float, nullable=False)

        cash_flow = relationship("CashFlow", back_populates="denominations")