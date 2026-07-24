import uuid
from datetime import date
from sqlalchemy import Text, UniqueConstraint, JSON
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, DateTime, Boolean, BINARY, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.opdp import PharmacyType
# from app.models.hospital import Hospital,HospitalBranch
from app.models.org import Hospital,Branch



# class EntryMedicine(Base):
#     __tablename__ = "entry_medicines"
#     id = Column(Integer, primary_key=True, index=True)
#     item_name = Column(String(255), index=True, nullable=False)
#     generic_name = Column(String(255), index=True)
#     # drug_combination = Column(String(255), index=True)
#     brand_name = Column(String(255), index=True)
#     category = Column(String(100), nullable=False)  #tablet/Syrup/Injection/Consumable/Surgical/NonSurgical
#     strength = Column(String(100), nullable=False)   #mg
#     #min_strength = Column(string(100), nullable=False)
#     #max_strengrh = Column(string(100), nullable=False)
#     dosage_form = Column(String(100), nullable=False)
#     price = Column(Integer,nullable=False)
#     company = Column(String(255),nullable=True)
#     hsn_code = Column(Integer, nullable=False)
#     batches = relationship("Batch", backref="medicine")
#     surgical_items = relationship("SurgicalItem", backref="medicine")
#     non_surgical_items = relationship("NonSurgicalItem", backref="medicine")
#     batches = relationship("Batch", back_populates="medicine")



class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer,ForeignKey("hospitals.id"),nullable=False,index=True)
    branch_id = Column(Integer,ForeignKey("branches.id"),nullable=False,index=True)
    # name = Column(String(255), nullable=False, index=True)
    item_name = Column(String(255))
    # medicine_name = Column(String(255), unique=True)
    generic_name = Column(String(255), index=True)
    brand_name = Column(String(255), index=True)
    category = Column(String(100))  # tablet/Syrup/Injection/etc
    dosage_form = Column(String(100))
    strength = Column(String(100))
    hsn_code = Column(String(50))
    is_restricted = Column(Boolean, default=False)
    is_discount_allowed = Column(Boolean, default=True)
    price = Column(Float)
    unit_price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    quantity = Column(Integer,nullable=False)
    min_stock = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    fast_moving = Column(Boolean, default=False)
    batch_no = Column(String(100))
    mfg_date = Column(Date)
    expiry_date = Column(Date,nullable=False)
    company = Column(String(255))
    description = Column(String(255))
    drug_formula = Column(String(255))
    # hospital = relationship("Hospital") 
    # branch = relationship("HospitalBranch")
    batches = relationship("Batch", back_populates="medicine")
    surgical_items = relationship("SurgicalItem",back_populates="medicine")
    non_surgical_items = relationship("NonSurgicalItem",back_populates="medicine")
    purchase_orders = relationship("PurchaseOrder",back_populates="medicine")


# class Batch(Base):
#     __tablename__ = "batches"
#     id = Column(Integer, primary_key=True, index=True)
#     hospital_id = Column(Integer, index=True)
#     branch_id = Column(Integer, index=True)
#     medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
#     strength = Column(String(225),nullable=False,index = True)
#     batch_number = Column(String(100), index=True, nullable=False)
#     manufacture_date = Column(Date, nullable=False)
#     expiry_date = Column(Date, nullable=False)
#     vendor_name = Column(String(255), nullable=False) 
#     invoice_number = Column(String(100), nullable=True)
#     po_number = Column(String(100), nullable=True)
#     quantity_received = Column(Integer, nullable=False)
#     quantity_available = Column(Integer, nullable=False, default=0)
#     mrp = Column(Float, nullable=False)
#     cost_price = Column(Float, nullable=False)
#     gst_percent = Column(Float, nullable=False)
#     cgst = Column(Float,nullable=False)
#     sgst = Column(Float,nullable=False)
#     discount_percent = Column(Float, nullable=False)
#     total_value = Column(Float, nullable=False)
#     rack_shelf_number = Column(String(100), nullable=True)
#     storage_condition = Column(String(50), nullable=False)  #normal/cold storage
#     medicine = relationship("Medicine", back_populates="batches")
#     __table_args__ = (
#         UniqueConstraint(
#             "medicine_id",
#             "batch_number",
#             "invoice_number",
#             name="uq_batch_unique"
#         ),
#     )
#     @property
#     def days_until_expiry(self) -> int:
#         return (self.expiry_date - date.today()).days  #expiry_date



class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, index=True)
    branch_id = Column(Integer, index=True)

    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)

    strength = Column(String(225), nullable=False, index=True)
    batch_number = Column(String(100), index=True, nullable=False)

    manufacture_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=False)

    vendor_name = Column(String(255), nullable=False)
    invoice_number = Column(String(100), nullable=True)
    po_number = Column(String(100), nullable=True)

    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False, default=0)
    returned_quantity = Column(Integer, default=0)

    mrp = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)

    gst_percent = Column(Float, nullable=False)
    cgst = Column(Float, nullable=False)
    sgst = Column(Float, nullable=False)

    discount_percent = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)

    rack_shelf_number = Column(String(100), nullable=True)
    storage_condition = Column(String(50), nullable=False)

    medicine = relationship("Medicine", back_populates="batches")

    __table_args__ = (
        UniqueConstraint(
            "medicine_id",
            "batch_number",
            "invoice_number",
            name="uq_batch_unique"
        ),
    )

    # EXPIRY LOGIC

    @property
    def days_until_expiry(self) -> int:
        return (self.expiry_date - date.today()).days

    @property
    def is_expired(self) -> bool:
        return self.expiry_date < date.today()

    @property
    def is_near_expiry(self) -> bool:
        return 0 <= self.days_until_expiry <= 30

    @property
    def is_expiry_60(self) -> bool:
        return 0 <= self.days_until_expiry <= 60

    @property
    def is_expiry_90(self) -> bool:
        return 0 <= self.days_until_expiry <= 90

   
    # BUSINESS RULE FLAGS

    @property
    def is_blocked(self) -> bool:
        return self.is_expired or self.is_near_expiry

    @property
    def is_locked(self) -> bool:
        return self.is_expired

    @property
    def can_return(self) -> bool:
        return self.quantity_available > 0 and (
            self.is_near_expiry or self.is_expired
        )
    
    # FINANCIAL

    @property
    def expiry_loss_value(self) -> float:
        if self.is_expired:
            return self.quantity_available * self.cost_price
        return 0.0


class StockLedger(Base):
    __tablename__ = "stockledger"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer,ForeignKey("hospitals.id"),nullable=False,index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    batch_type = Column(String(20), nullable=False)
    batch_id = Column(Integer, nullable=False)#ForeignKey("batches.id"))
    transaction_type = Column(String(50), nullable=False)  #OPENING/RECEIPT/ISSUE/ADJUSTMENT
    quantity_in = Column(Integer, default=0)
    quantity_out = Column(Integer, default=0)
    balance_qty = Column(Integer, nullable=False)
    transaction_value = Column(Float, default=0.0)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    remarks = Column(String(255), nullable=True)
    # batch = relationship("Batch")


# class PharmacyIssue(Base):
#     __tablename__ = "pharmacy_issues"
#
#     id = Column(Integer, primary_key=True, index=True)
#
#     hospital_id = Column(Integer, nullable=False, index=True)
#     branch_id = Column(Integer, nullable=False, index=True)
#
#     # Core issue context
#     pharmacy_type = Column(Enum(PharmacyType), nullable=True)
#     item_type = Column(String(20))  # medicine|surgical|non_surgical
#     item_id = Column(Integer)  # medicine_id OR surgical_item_id OR non_surgical_item_id
#     medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)
#     batch_type = Column(String(20))  # medicine|surgical|non_surgical
#     batch_id = Column(Integer)  # Specific batch ID
#
#     # Patient / reference context
#     patient_type = Column(String(20))  # IPD|OPD|Emergency
#     patient_name = Column(String(100))
#     patient_id_proof = Column(String(50))
#     patient_uhid = Column(String(50), index=True)  # from WardMedicineIssue
#     ward_id = Column(String(20))  # from WardMedicineIssue
#     reference_id = Column(Integer)  # Patient ID, Bill ID, etc.
#
#     # Prescription / order context
#     prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)  # from third
#
#     # Quantities and values
#     quantity = Column(Integer)
#     rate_per_unit = Column(Float)
#     issue_value = Column(Float)  # from first
#     total_amount = Column(Float, default=0.0)  # from WardMedicineIssue
#
#     # Staff / workflow
#     issued_by = Column(String(100))  # Staff ID/Name
#     pharmacist_id = Column(Integer)  # from WardMedicineIssue
#     pharmacist_sign = Column(String(100))
#     issued_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
#
#     # Ward‑style JSON payload (you can keep this or normalize later)
#     medicines_json = Column(Text)  # from WardMedicineIssue
#     remarks = Column(String(255))
#
#     # NOC / payments / refunds (from WardMedicineIssue)
#     noc_number = Column(String(50))
#     payment_mode = Column(String(20), default="cash")
#     cash_denominations_json = Column(Text)
#     card_txn_ref = Column(String(50))
#     is_refunded = Column(Boolean, default=False)
#     refund_amount = Column(Float, default=0.0)
#
#     # Soft delete / cancellation
#     is_cancelled = Column(Boolean, default=False)
#     cancelled_at = Column(DateTime(timezone=True))
#     cancelled_by = Column(String(100))
#
#     # UUID‑style reference (from WardMedicineIssue)
#     issue_ref = Column(BINARY(16), default=lambda: uuid.uuid4().bytes, unique=True, index=True)

class PharmacyIssue(Base):
    __tablename__ = "pharmacy_issues"

    id = Column(Integer, primary_key=True, index=True)

    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)

    # ---------------------------
    # ITEM STRUCTURE (CLEANED)
    # ---------------------------
    item_type = Column(
        Enum("medicine", "surgical", "non_surgical", name="item_type_enum"),
        nullable=False,
        index=True
    )
    pharmacy_type = Column(Enum(PharmacyType), nullable=True)
    item_id = Column(Integer, nullable=True, index=True)
    batch_id = Column(Integer, nullable=False, index=True)
    batch_type = Column(
        String(50),
        nullable=False,
        index=True
    )

    # Optional FK only for medicine
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)

    # ---------------------------
    # PATIENT INFO
    # ---------------------------
    patient_type = Column(String(20), nullable=False)
    patient_name = Column(String(100))
    patient_id_proof = Column(String(50))
    patient_uhid = Column(String(50), index=True)
    ward_id = Column(String(20))
    reference_id = Column(Integer)

    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    visit_id = Column(
        Integer,
        ForeignKey("opd_visits.id"),
        nullable=True,
        index=True
    )

    # ---------------------------
    # QUANTITIES
    # ---------------------------
    quantity = Column(Integer, nullable=False)
    rate_per_unit = Column(Float, nullable=True)
    issue_value = Column(Float, nullable=True)
    total_amount = Column(Float, default=0.0)

    # ---------------------------
    # STAFF
    # ---------------------------
    issued_by = Column(String(100), nullable=False)
    pharmacist_id = Column(Integer, nullable=False)
    pharmacist_sign = Column(String(100))

    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ---------------------------
    # JSON (FIXED LATER)
    # ---------------------------
    medicines_json = Column(JSON, nullable=True)
    cash_denominations_json = Column(JSON, nullable=True)

    remarks = Column(String(255))

    # ---------------------------
    # PAYMENT
    # ---------------------------
    noc_number = Column(String(50))
    payment_mode = Column(String(20), default="cash")
    card_txn_ref = Column(String(50))

    is_refunded = Column(Boolean, default=False)
    refund_amount = Column(Float, default=0.0)

    # ---------------------------
    # CANCEL
    # ---------------------------
    is_cancelled = Column(Boolean, default=False)
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(String(100))

    # ---------------------------
    # UUID REF
    # ---------------------------
    issue_ref = Column(
        BINARY(16),
        default=lambda: uuid.uuid4().bytes,
        unique=True,
        index=True
    )

class SurgicalItem(Base):
    __tablename__ = "surgical_items"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)  # Optional link to medicine
    item_code = Column(String(100), unique=True, index=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    item_type = Column(String(100), nullable=False)  #Suture/Glove/Mask/Instrument/Drains/Dressings
    size_specification = Column(String(100))  #Gauge/Size/Color for surgical items
    sterility_status = Column(String(50), nullable=False)  # Sterile/Non-Sterile
    usage_count_per_procedure = Column(Integer, default=1)
    unit_of_measure = Column(String(50), nullable=False)  # Pcs/Pack/Box
    batches = relationship("SurgicalBatch", backref="surgical_item")

    medicine = relationship("Medicine", back_populates="surgical_items")

class SurgicalBatch(Base):
    __tablename__ = "surgical_batches"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    surgical_item_id = Column(Integer, ForeignKey("surgical_items.id"), nullable=False)
    batch_number = Column(String(100), index=True, nullable=False)
    manufacture_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)  #some surgical items not expire
    vendor_name = Column(String(255), nullable=False)
    invoice_number = Column(String(100), nullable=True)
    po_number = Column(String(100), nullable=True)
    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False, default=0)
    mrp = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    gst_percent = Column(Float, nullable=False)
    cgst = Column(Float,nullable=False)
    sgst = Column(Float,nullable=False)
    discount_percent = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    sterilization_date = Column(Date, nullable=True)
    rack_shelf_number = Column(String(100), nullable=True)
    storage_condition = Column(String(50), nullable=False)


class NonSurgicalItem(Base):
    __tablename__ = "non_surgical_items"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True) #optional
    item_code = Column(String(100), unique=True, index=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    item_type = Column(String(100), nullable=False)  #disposable/durable/consumable
    specification = Column(String(100))  #size/type/material
    usage_per_patient = Column(Float, default=1.0)
    unit_of_measure = Column(String(50), nullable=False)  #pcs/pack/ml
    batches = relationship("NonSurgicalBatch", backref="non_surgical_item")
    medicine = relationship("Medicine", back_populates="non_surgical_items")

class NonSurgicalBatch(Base):
    __tablename__ = "non_surgical_batches"
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, nullable=False, index=True)
    branch_id = Column(Integer, nullable=False, index=True)
    non_surgical_item_id = Column(Integer, ForeignKey("non_surgical_items.id"), nullable=False)
    batch_number = Column(String(100), index=True, nullable=False)
    manufacture_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)  #many non-surgical don't expire
    vendor_name = Column(String(255), nullable=False)
    invoice_number = Column(String(100), nullable=True)
    po_number = Column(String(100), nullable=True)
    quantity_received = Column(Integer, nullable=False)
    quantity_available = Column(Integer, nullable=False, default=0)
    mrp = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    gst_percent = Column(Float, nullable=False)
    cgst = Column(Float, nullable=False)
    sgst = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    rack_shelf_number = Column(String(100), nullable=True)
    storage_condition = Column(String(50), nullable=False)


























