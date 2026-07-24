from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime, UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.db.base import Base



class HospitalInvoice(Base):
    __tablename__ = "hospital_invoices"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    invoice_number = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    currency = Column(String(50), default="INR")

    subtotal = Column(Float)
    discount_pct = Column(Float, default=0)
    discount_value = Column(Float, default=0)
    discount_reason = Column(String(255), nullable=True)
    tax_pct = Column(Float, default=0)
    tax_value = Column(Float, default=0)
    total = Column(Float)
    paid = Column(Float, default=0)
    due = Column(Float, default=0)

    patient_name = Column(String(100), nullable=False)
    patient_gender = Column(String(20), nullable=False)
    patient_dob = Column(String(50), nullable=False)

    referral_name = Column(String(100), nullable=True)
    referral_amount = Column(Float, default=0)
    file_key = Column(String(300), nullable=True)

    __table_args__ = (
        UniqueConstraint("appointment_id", name="uq_invoice_appointment"),
    )

    appointment = relationship("Appointment", back_populates="invoice")  # ← added
    items = relationship("HospitalInvoiceItem", back_populates="invoice", cascade="all, delete")
    payments = relationship("HospitalInvoicePayment", back_populates="invoice", cascade="all, delete")


class HospitalInvoiceItem(Base):
    __tablename__ = "hospital_invoice_items"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("hospital_invoices.id", ondelete="CASCADE"),
        nullable=False
    )

    description = Column(String(255), nullable=False)

    qty = Column(Integer, default=1)
    unit_price = Column(Float, default=0)
    line_total = Column(Float, default=0)

    invoice = relationship(
        "HospitalInvoice",
        back_populates="items"
    )

    def __repr__(self):
        return f"<HospitalInvoiceItem(id={self.id}, invoice_id={self.invoice_id})>"


class HospitalInvoicePayment(Base):
    __tablename__ = "hospital_invoice_payments"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(
        Integer,
        ForeignKey("hospital_invoices.id", ondelete="CASCADE"),
        nullable=False
    )

    amount = Column(Float, nullable=False)

    method = Column(String(100), nullable=True)

    ref = Column(String(100), nullable=True)

    date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    invoice = relationship(
        "HospitalInvoice",
        back_populates="payments"
    )

    def __repr__(self):
        return f"<HospitalInvoicePayment(id={self.id}, invoice_id={self.invoice_id})>"