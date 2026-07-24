from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    ForeignKey, Float, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy import JSON
from datetime import datetime
from app.db.base import Base
import enum




class MedicineCategory(enum.Enum):
    OTC = "OTC"
    SCHEDULE_H = "H"
    SCHEDULE_H1 = "H1"
    SCHEDULE_X = "X"

# class Medicine(Base):
#     __tablename__ = "medicines"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(150), nullable=False)
#     strength = Column(String(50))
#     category = Column(Enum(MedicineCategory), nullable=False)
#     is_discount_allowed = Column(Boolean, default=True)
#
#     batches = relationship("Batch", back_populates="medicine")

# class Batch(Base):
#     __tablename__ = "batches"
#
#     id = Column(Integer, primary_key=True)
#     medicine_id = Column(Integer, ForeignKey("medicines.id"))
#     batch_no = Column(String(50))
#     expiry_date = Column(Date)
#     quantity = Column(Integer)
#
#     medicine = relationship("Medicine", back_populates="batches")

# class Patient(Base):
#     __tablename__ = "patients"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100))
#     mobile = Column(String(15))
#     id_proof = Column(String(50))

# class Prescription(Base):
#     __tablename__ = "prescriptions"
#
#     id = Column(Integer, primary_key=True)
#     doctor_name = Column(String(100))
#     registration_no = Column(String(50))
#     prescription_date = Column(Date)
#     image_path = Column(String(255))
#     patient_id = Column(Integer, ForeignKey("patients.id"))
#
#     patient = relationship("Patient")


# class Sale(Base):
#     __tablename__ = "sales"
#
#     id = Column(Integer, primary_key=True)
#     prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
#     payment_mode = Column(String(20))
#     denominations = Column(JSON, nullable=True)
#     total_amount = Column(Float)
#     created_at = Column(DateTime, default=datetime.utcnow)


# class SaleItem(Base):
#     __tablename__ = "sale_items"
#
#     id = Column(Integer, primary_key=True)
#     sale_id = Column(Integer, ForeignKey("sales.id"))
#     medicine_id = Column(Integer, ForeignKey("medicines.id"))
#     batch_id = Column(Integer, ForeignKey("batches.id"))
#     quantity = Column(Integer)
#     price = Column(Float)



class CashFlow(Base):
    __tablename__ = "cash_flow"

    id = Column(Integer, primary_key=True, index=True)
    reference_type = Column(String(225), nullable=False)  # PHARMACY / OPD
    reference_id = Column(Integer, nullable=False)

    payment_mode = Column(String(225), nullable=False)  # CASH / UPI
    amount = Column(Float, nullable=False)

    upi_app = Column(String(225), nullable=True)  # GPay, PhonePe, Paytm
    created_by = Column(String(225), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    denominations = relationship(
        "CashDenomination",
        back_populates="cash_flow",
        uselist=False
    )



# class CashDenomination(Base):
#         __tablename__ = "cash_denominations"
#
#         id = Column(Integer, primary_key=True, index=True)
#         cash_flow_id = Column(Integer, ForeignKey("cash_flow.id"))
#         note_2000 = Column(Integer, default=0)
#         note_500 = Column(Integer, default=0)
#         note_200 = Column(Integer, default=0)
#         note_100 = Column(Integer, default=0)
#         note_50 = Column(Integer, default=0)
#         note_20 = Column(Integer, default=0)
#         note_10 = Column(Integer, default=0)
#         coins = Column(Float, default=0)
#
#         total_cash = Column(Float, nullable=False)
#
#         cash_flow = relationship("CashFlow", back_populates="denominations")