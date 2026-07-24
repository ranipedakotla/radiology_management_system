from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class Ward(Base):
    __tablename__ = "wards"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  #"GEN", "ICU"
    name = Column(String(100), nullable=False)  #"General Ward"
    is_active = Column(Boolean, default=True)


class WardMedicineIssue(Base):
    __tablename__ = "ward_medicine_issues"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    issue_ref = Column(BINARY(16), default=lambda: uuid.uuid4().bytes, unique=True, index=True)
    patient_uhid = Column(String(50), index=True, nullable=False)
    ward_id = Column(String(20), nullable=False)
    pharmacist_id = Column(Integer, nullable=False)
    medicines_json = Column(Text, nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(String(20), default="issued")
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    #noc,payments,refunds
    noc_number = Column(String(50), nullable=True)
    payment_mode = Column(String(20), default="cash")
    cash_denominations_json = Column(Text, nullable=True)
    card_txn_ref = Column(String(50), nullable=True)
    is_refunded = Column(Boolean, default=False)
    refund_amount = Column(Float, default=0.0)
#

class MedicineReturn(Base):
    __tablename__ = "medicine_returns"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    return_ref = Column(BINARY(16), default=lambda: uuid.uuid4().bytes, unique=True, index=True)
    issue_ref = Column(BINARY(16), nullable=False)
    patient_uhid = Column(String(50), nullable=False)
    return_items_json = Column(Text, nullable=False)
    reason = Column(String(100), nullable=False)
    pharmacist_id = Column(Integer, nullable=False)
    status = Column(String(20), default="accepted")
    returned_at = Column(DateTime(timezone=True), server_default=func.now())

    #noc,refund payments
    noc_number = Column(String(50), nullable=True)
    refund_mode = Column(String(20), default="cash")
    refund_denominations_json = Column(Text, nullable=True)
    refund_card_txn_ref = Column(String(50), nullable=True)
