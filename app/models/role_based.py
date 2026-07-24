from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    Float,
    ForeignKey,
    Date
)
from app.db.base import Base

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(300), nullable=False)
#     email = Column(String(100), unique=True)
#     password = Column(String(255), nullable=False)
#     role = Column(String(30),nullable=False)
#     is_active = Column(Boolean, default=True)


# class ShiftLog(Base):
#
#     __tablename__ = "shift_logs"
#
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     shift_type = Column(String(20))  # DAY / EVENING / NIGHT
#     login_time = Column(DateTime)
#     logout_time = Column(DateTime)
#     total_sales = Column(Integer, default=0)

class BillingSummary(Base):
        __tablename__ = "billing_summary"
        id = Column(Integer, primary_key=True)
        hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
        branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
        # medicine_name = Column(String(100), nullable=False)
        shift_id = Column(Integer, ForeignKey("shift_logs.id"))
        appointment_id = Column(
            Integer,
            ForeignKey("appointments.id"),
            nullable=False,
            index=True
        )
        bill_date = Column(Date)
        cash_amount = Column(Float, default=0)
        upi_amount = Column(Float, default=0)
        card_amount = Column(Float, default=0)
        total_amount = Column(Float)


class Payroll(Base):
    __tablename__ = "payroll"
    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    base_salary = Column(Float)
    shift_allowance = Column(Float)
    night_allowance = Column(Float)
    overtime_pay = Column(Float)
    incentive = Column(Float)
    total_salary = Column(Float)