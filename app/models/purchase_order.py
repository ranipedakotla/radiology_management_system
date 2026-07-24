from sqlalchemy import Boolean, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False)

    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"))

    quantity = Column(Integer, nullable=False)
    rate = Column(Float, nullable=False)
    discount = Column(Float, default=0)
    gst = Column(Float, default=0)

    delivery_location = Column(String(255))
    delivery_deadline = Column(Date)
    terms = Column(String(255))
    is_posted = Column(Boolean, default=False)

    vendor = relationship("Vendor")
    medicine = relationship("Medicine")
