from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean, Text, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"))
    name = Column(String(150), nullable=False)
    contact = Column(String(120))
    contact_person = Column(String(150), nullable=True)
    vendor_category = Column(String(200),nullable= True)
    account_number = Column(String(200),nullable= True)
    drug_license_number = Column(String(100), nullable=True)
    ifsc_code = Column(String(200),nullable=True)
    email = Column(String(120))
    payment_terms = Column(String(120))
    address = Column(Text)
    gst_no = Column(String(20), index=True, nullable=True)
    emergency_contact = Column(String(15))
    pincode = Column(String(10))
    delivery_timeliness =Column(Integer)
    medicine_quality = Column(Integer)
    price_consistency = Column(Integer)
    expiry_risk = Column(Integer)
    payment_history = Column(Integer)
    status = Column(String(50),default="pending")
    products_available = Column(Text)
    is_active = Column(Boolean, default=True)

    quotations = relationship(
        "Quotation",
        back_populates="vendor",
        cascade="all, delete-orphan"
    )

# class Medicine(Base):
#     __tablename__ = "medicines"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     strength = Column(String(255))
#     dosage_form = Column(String(100))
#     expire_date = Column(Date)
#     quantity = Column(Integer)
#     Description = Column(String(255))
#     Drug_formula = Column(String(255))


#
# class PurchaseOrder(Base):
#     __tablename__ = "purchase_orders"
#
#     id = Column(Integer, primary_key=True)
#     po_number = Column(String(50), unique=True)
#     vendor_id = Column(Integer, ForeignKey("vendors.id"), index=True)
#     medicine_id = Column(Integer, ForeignKey("medicines.id"), index=True)
#     quantity = Column(Integer)
#     rate = Column(Float)
#     discount = Column(Float)
#     gst = Column(Float)
#     delivery_location = Column(String(60))
#     delivery_deadline = Column(Date)
#     terms = Column(Text)
#     vendor = relationship("Vendor")
#     #  medicine = relationship("Medicine")


class VendorTransaction(Base):
    __tablename__ = "vendor_transactions"

    id = Column(Integer, primary_key=True, index=True)

    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    hospital_id = Column(Integer, nullable=False)
    branch_id = Column(Integer, nullable=False)

    type = Column(String(225), nullable=False)  # "credit" or "debit"
    amount = Column(Float, nullable=False)

    reference = Column(String(225), nullable=True)  # invoice/payment ref
    notes = Column(String(225), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())



#
# class VendorReturn(Base):
#     __tablename__ = "vendor_returns"
#
#     id = Column(Integer, primary_key=True)
#
#     hospital_id = Column(Integer, ForeignKey("hospitals.id"))
#     branch_id = Column(Integer, ForeignKey("hospital_branches.id"))
#
#     vendor_id = Column(
#         Integer,
#         ForeignKey("vendors.id"),
#         nullable=False
#     )
#
#     grn_id = Column(
#         Integer,
#         ForeignKey("grn.id"),
#         nullable=True
#     )
#
#     return_number = Column(String, unique=True)
#
#     reason = Column(String)
#
#     status = Column(String, default="PENDING")
#
#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow
#     )
#
#     items = relationship(
#         "VendorReturnItem",
#         back_populates="vendor_return",
#         cascade="all, delete-orphan"
#     )
#
#
#
#
#
# class VendorReturnItem(Base):
#     __tablename__ = "vendor_return_items"
#
#     id = Column(Integer, primary_key=True)
#
#     vendor_return_id = Column(
#         Integer,
#         ForeignKey("vendor_returns.id", ondelete="CASCADE")
#     )
#
#     batch_id = Column(
#         Integer,
#         ForeignKey("batches.id")
#     )
#
#     medicine_id = Column(
#         Integer,
#         ForeignKey("entry_medicines.id")
#     )
#
#     quantity = Column(Integer)
#
#     reason = Column(String)
#
#     vendor_return = relationship(
#         "VendorReturn",
#         back_populates="items"
#     )
#
#     batch = relationship("Batch")