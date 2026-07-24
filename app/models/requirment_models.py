from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


# class PharmacyMedicine(Base):
#     __tablename__ = "pharmacy_medicine"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(150), nullable=False)
#     stock = Column(Integer, default=0)
#     reorder_level = Column(Integer, default=10)
#     fast_moving = Column(Boolean, default=False)
#     expiry_date = Column(Date)
#     batch_no = Column(String(50), nullable=True)
#     unit_price = Column(Float, nullable=True)
#

# class Vendor(Base):
#     __tablename__ = "vendors"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(150), nullable=False)
#     contact = Column(String(120))
#     email = Column(String(120))
#     payment_terms = Column(String(120))


class RequestQuotation(Base):
    __tablename__ = "requesting_quotations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("pharmacy_medicine.id"),nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"),nullable=False)
    rate_per_unit = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)
    gst_percent = Column(Float, default=0)
    mrp = Column(Float, nullable=False)
    available_batch = Column(String(50))
    expiry_date = Column(Date)
    delivery_time_days = Column(Integer)

    medicine = relationship("PharmacyMedicine")
    vendor = relationship("Vendor")
