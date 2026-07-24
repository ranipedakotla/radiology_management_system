# models/grn.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class GRN(Base):
    __tablename__ = "grns"

    id = Column(Integer, primary_key=True, index=True)

    grn_number = Column(String(50), unique=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    po_id = Column(Integer, ForeignKey("purchase_orders.id"))

    hospital_id = Column(Integer)
    branch_id = Column(Integer)

    invoice_number = Column(String(100))
    received_by = Column(String(100))
    received_date = Column(DateTime, default=datetime.utcnow)

    remarks = Column(Text, nullable=True)

    vendor = relationship("Vendor")
    items = relationship("GRNItem", back_populates="grn", cascade="all, delete-orphan")

class GRNItem(Base):
        __tablename__ = "grn_items"

        id = Column(Integer, primary_key=True, index=True)

        grn_id = Column(Integer, ForeignKey("grns.id"))
        medicine_id = Column(Integer, ForeignKey("medicines.id"))

        ordered_qty = Column(Integer)
        received_qty = Column(Integer)
        damaged_qty = Column(Integer, default=0)

        batch_number = Column(String(100))
        expiry_date = Column(DateTime)

        grn = relationship("GRN", back_populates="items")