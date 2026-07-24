from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Time
from datetime import datetime
from app.db.base import Base

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(100), unique=True, index=True, nullable=False)
#     email = Column(String(100), unique=True, index=True)
#     hashed_password = Column(String(255), nullable=False)
#     role = Column(String(50), nullable=False, index=True)  # SUPERADMIN
#     is_active = Column(Boolean, default=True)
#     active_session_id = Column(String(64), nullable=True)
#     created_at = Column(DateTime, server_default=func.now())
#     hospital_id = Column(
#         Integer,
#         ForeignKey("hospitals.id"),
#         nullable=False,
#         index=True
#     )
#
#     branch_id = Column(
#         Integer,
#         ForeignKey("branches.id"),
#         nullable=False,
#         index=True
#     )
#
#     # shifts = relationship("ShiftLog", back_populates="pharmacist")
#     assigned_shifts = relationship("UserShift", back_populates="user")
#     sales = relationship("Sale", back_populates="pharmacist")
#     shifts = relationship("ShiftLog",back_populates="pharmacist",foreign_keys="ShiftLog.pharmacist_id")
#     hospital = relationship("Hospital")
#     branches = relationship("Branch")

class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  #A,B,C,D
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    shift_logs = relationship("ShiftLog", back_populates="shift")

class UserShift(Base):
    __tablename__ = "user_shifts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    assigned_date = Column(Date, nullable=False)
    user = relationship("User", back_populates="assigned_shifts")
    shift = relationship("Shift")

class ShiftLog(Base):
    __tablename__ = "shift_logs"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False)
    branch_id = Column(Integer, nullable=False)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    shift_type = Column(String(20))  # DAY / EVENING / NIGHT
    # login_time = Column(DateTime)
    # logout_time = Column(DateTime)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_sales = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    sales_amount = Column(Float, default=0.0)

    # pharmacist = relationship("User", back_populates="shifts")
    pharmacist = relationship(
        "User",
        back_populates="shifts",
        foreign_keys="ShiftLog.pharmacist_id"  
    )
    shift = relationship("Shift", back_populates="shift_logs")


# class Medicine(Base):
#     __tablename__ = "medicines"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(200), index=True, nullable=False)
#     is_restricted = Column(Boolean, default=False)
#     stock = Column(Integer, default=0)
#     min_stock = Column(Integer, default=0)

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shift_log_id = Column(Integer, ForeignKey("shift_logs.id"), nullable=True)
    patient_type = Column(String(20))
    patient_id = Column(Integer, nullable=True)
    total_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    payment_mode = Column(String(20))
    denominations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pharmacist = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")

# class Prescription(Base):
#     __tablename__ = "prescriptions"
#
#     id = Column(Integer, primary_key=True, index=True)
#     hospital_id = Column(Integer, nullable=False)
#     branch_id = Column(Integer, nullable=False)
#     doctor_name = Column(String(100))
#     doctor_reg_no = Column(String(50))
#     registration_no = Column(String(50))
#     prescription_date = Column(Date)
#     image_url = Column(String(255))
#     image_path = Column(String(255))
#     patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
#     pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     filename = Column(String(255), nullable=False)
#     content_type = Column(String(100), nullable=False)
#     file_path = Column(String(500), nullable=False)
#     uploaded_at = Column(DateTime, default=datetime.utcnow)
#
#     patient = relationship("Patient")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    patient_id = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(String(255), nullable=True)

    pharmacist = relationship(
        "User",
        foreign_keys=[pharmacist_id]
    )

    manager = relationship(
        "User",
        foreign_keys=[manager_id]
    )

    medicine = relationship("Medicine")

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id = Column(Integer, primary_key=True, index=True)
    pharmacist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    pharmacist = relationship("User", foreign_keys=[pharmacist_id])
    medicine = relationship("Medicine")
