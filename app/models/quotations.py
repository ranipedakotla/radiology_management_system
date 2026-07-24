from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Date, Boolean
)
from sqlalchemy.orm import relationship
from app.db.base import Base

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(200), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"))
    # quotation_id = Column(Integer, ForeignKey("quotations.id"))
    drug_license_no = Column(String(100), nullable=False)
    gst_no = Column(String(50), nullable=False)
    place_of_supply = Column(String(100), nullable=False)
    invoice_no =Column(String(100), nullable=False)
    quotation_date = Column(Date)
    total_amount = Column(Float, default=0)
    total_discount = Column(Float, default=0)
    net_amount = Column(Float, default=0)
    is_approved = Column(Boolean, default=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)

    vendor = relationship("Vendor", back_populates="quotations")
    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete"
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"))
    hospital_id = Column(Integer)
    branch_id = Column(Integer)

    medicine_name = Column(String(200), nullable=False)
    dosage = Column(String(50))          # 500mg, 250mg, syrup 100ml
    quantity = Column(Integer, nullable=False)

    mrp = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    cgst = Column(Float, default=0)
    sgst = Column(Float, default=0)

    total_price = Column(Float, nullable=False)
    discount_price = Column(Float, default=0)
    final_price = Column(Float, nullable=False)

    quotation = relationship("Quotation", back_populates="items")
