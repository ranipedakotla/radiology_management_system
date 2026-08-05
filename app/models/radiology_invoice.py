from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base  # adjust import to match your existing Base location


class Patient(Base):
    __tablename__ = "Invoice_patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    op_ip_number = Column(String(50), unique=True, index=True)
    age = Column(Integer)
    gender = Column(String(10))
    mobile = Column(String(20))

    invoices = relationship("Invoice", back_populates="patient")


class Invoice(Base):
    __tablename__ = "radiology_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, index=True, nullable=False)
    date = Column(String(20))
    time = Column(String(20))
    bill_type = Column(String(20))
    notes = Column(Text)
    terms = Column(Text)
    generated_by = Column(String(100))
    generated_on = Column(DateTime, default=datetime.utcnow)
    signatory_name = Column(String(100))

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    patient = relationship("Patient", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    insurance = relationship("InsuranceDetail", back_populates="invoice", uselist=False, cascade="all, delete-orphan")
    payment = relationship("PaymentDetail", back_populates="invoice", uselist=False, cascade="all, delete-orphan")
    billing = relationship("BillingSummary", back_populates="invoice", uselist=False, cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "radiology_invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    qty = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    amount = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class InsuranceDetail(Base):
    __tablename__ = "insurance_details"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    status = Column(String(30))
    provider = Column(String(255))
    policy_no = Column(String(50))
    approval_no = Column(String(50))
    coverage_split = Column(String(100))

    invoice = relationship("Invoice", back_populates="insurance")


class PaymentDetail(Base):
    __tablename__ = "payment_details"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    status = Column(String(30))
    mode = Column(String(100))
    transaction_id = Column(String(50))
    collected_by = Column(String(100))

    invoice = relationship("Invoice", back_populates="payment")


class BillingSummary(Base):
    __tablename__ = "billing_summaries"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    subtotal = Column(Float, nullable=False)
    total_discount = Column(Float, default=0.0)
    taxable_amount = Column(Float, nullable=False)
    gst = Column(Float, default=0.0)
    grand_total = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    balance_amount = Column(Float, default=0.0)
    invoice = relationship("Invoice", back_populates="billing")