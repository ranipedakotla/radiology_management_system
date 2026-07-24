from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, Text, UniqueConstraint,Boolean,Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


from app.models._mixins import TenantedMixin


class PriceList(Base):
    __tablename__ = "price_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    test_prices = relationship("PriceListTest", back_populates="price_list", cascade="all, delete-orphan")
    panel_prices = relationship("PriceListPanel", back_populates="price_list", cascade="all, delete-orphan")


class PriceListTest(Base):
    __tablename__ = "price_list_tests"
    __table_args__ = (UniqueConstraint("price_list_id", "test_id", name="uq_pricelist_test"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("price_lists.id", ondelete="CASCADE"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(Float)

    price_list = relationship("PriceList", back_populates="test_prices")


class PriceListPanel(Base):
    __tablename__ = "price_list_panels"
    __table_args__ = (UniqueConstraint("price_list_id", "panel_id", name="uq_pricelist_panel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("price_lists.id", ondelete="CASCADE"))
    panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(Float)

    price_list = relationship("PriceList", back_populates="panel_prices")


class Invoice(Base, TenantedMixin):
    __tablename__ = "invoices"

    __table_args__ = (UniqueConstraint("branch_id", "invoice_no", name="uq_invoices_branch_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("opd_visits.id"), nullable=True, index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True, index=True)

    patient_name = mapped_column(String(100), nullable=False)
    gender = mapped_column(String(20), nullable=False)
    patient_dob = mapped_column(String(50), nullable=False)

    invoice_no: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|issued|partially_paid|paid|void

    sub_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    discount_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    tax_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    # ...
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_url:  Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["InvoiceItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base,TenantedMixin):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)

    item_type: Mapped[str] = mapped_column(String(30))   # consultation|lab|service|medicine
    ref_id: Mapped[int | None]
    description: Mapped[str] = mapped_column(String(255))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class Receipt(Base, TenantedMixin):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)

    amount_received: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    mode: Mapped[str] = mapped_column(String(20))  # Cash | UPI | Card
    utr_no: Mapped[str | None] = mapped_column(String(80), nullable=True)

    cash_500: Mapped[int] = mapped_column(Integer, default=0)
    cash_200: Mapped[int] = mapped_column(Integer, default=0)
    cash_100: Mapped[int] = mapped_column(Integer, default=0)
    cash_50: Mapped[int] = mapped_column(Integer, default=0)
    cash_20: Mapped[int] = mapped_column(Integer, default=0)
    cash_10: Mapped[int] = mapped_column(Integer, default=0)
    cash_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))

    notes: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice: Mapped[Invoice] = relationship(back_populates="receipts")


class PathologyInvoice(Base):
    __tablename__ = "Pathology_invoice"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id", ondelete="CASCADE"))
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_pct: Mapped[float] = mapped_column(Float, default=0)
    discount_value: Mapped[float] = mapped_column(Float, default=0)
    tax_pct: Mapped[float] = mapped_column(Float, default=0)
    tax_value: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)
    due: Mapped[float] = mapped_column(Float, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ✅ add these three mapped columns
    s3_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qr_code_token: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    # invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    invoice_id = mapped_column(
        ForeignKey("Pathology_invoice.id")
    )
    item_type: Mapped[str] = mapped_column(String(8))  # "test" or "panel"
    ref_id: Mapped[int] = mapped_column(Integer)  # test_id or panel_id
    description: Mapped[str] = mapped_column(String(128))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    line_total: Mapped[float] = mapped_column(Float, default=0)

    invoice = relationship("PathologyInvoice", back_populates="lines")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(16))  # cash/card/upi/online
    txn_ref: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(String(128))
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recorded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pathology_invoice_id = mapped_column(
        ForeignKey("Pathology_invoice.id")
    )
    invoice = relationship(
        "PathologyInvoice",
        back_populates="payments"
    )
    # invoice = relationship("Invoice", back_populates="payments")
