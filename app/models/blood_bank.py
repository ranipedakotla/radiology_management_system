from sqlalchemy import (
    Column, Integer, String, Date, Enum,
    ForeignKey, Boolean, Index, DateTime,Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
from enum import Enum as PyEnum

# ===================== ENUMS =====================

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    LAB_TECH = "LAB_TECH"
    BLOOD_BANK_STAFF = "BLOOD_BANK_STAFF"
    SUPERADMIN = "SUPERADMIN"
    DRIVER ="DRIVER"
    DOCTOR = "DOCTOR"
    RECEPTIONIST = "RECEPTIONIST"

class TestStatus(str, PyEnum):
    PENDING = "PENDING"
    TESTED = "TESTED"
    AVAILABLE = "AVAILABLE"
    REJECTED = "REJECTED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"


class BloodStatus(str, enum.Enum):
    PENDING_LAB = "PENDING_LAB"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    REJECTED = "REJECTED"
    MATCHED = "MATCHED"
    COMPLETED = "COMPLETED"


class ComponentType(str, enum.Enum):
    RBC = "RBC"
    PLASMA = "PLASMA"
    PLATELETS = "PLATELETS"


# ===================== USER =====================

# class User(Base):
#     __tablename__ = "users"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     email = Column(String(100), unique=True, index=True, nullable=False)
#     hashed_password = Column(String(255), nullable=False)
#     role = Column(Enum(UserRole), nullable=False)
#     is_active = Column(Boolean, default=True)
#
#     created_at = Column(DateTime, server_default=func.now())
#     updated_at = Column(DateTime, onupdate=func.now())


# ===================== DONOR =====================

class Donor(Base):
    __tablename__ = "blood_donors"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=False)
    address = Column(String(255), nullable=False)
    blood_group = Column(String(5), nullable=False)
    gender = Column(String(10))
    age = Column(Integer, nullable=False)
    has_donated = Column(Boolean, default=False)  # 👈 THIS
    last_donation_date = Column(Date, nullable=True)

    # Exchange related
    wants_exchange = Column(Boolean, default=False)
    exchange_blood_group = Column(String(5), nullable=False)

    # Eligibility
    eligibility = Column(String(20), nullable=True)
    eligibility_checked_at = Column(DateTime, nullable=True)
    eligibility_checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    collections = relationship(
        "BloodCollection",
        back_populates="donor",
        cascade="all, delete-orphan"
    )


# ===================== BLOOD COLLECTION =====================

class BloodCollection(Base):
    __tablename__ = "blood_collections"

    id = Column(Integer, primary_key=True, index=True)

    donor_id = Column(
        Integer,
        ForeignKey("blood_donors.id", ondelete="CASCADE"),
        nullable=False
    )

    collection_date = Column(Date, nullable=False)

    test_status = Column(
        Enum(TestStatus),
        default=TestStatus.PENDING
    )

    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    donor = relationship("Donor", back_populates="collections")

    inventory = relationship(
        "BloodInventory",
        back_populates="collection",
        cascade="all, delete-orphan"
    )

    test_report = relationship(
        "BloodTestReport",
        back_populates="collection",
        uselist=False,
        cascade="all, delete-orphan"
    )

# ===================== BLOOD INVENTORY =====================

class BloodInventory(Base):
    __tablename__ = "blood_stock"

    __table_args__ = (
        Index(
            "idx_inventory_group_component_status",
            "blood_group",
            "component_type",
            "status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(
        Integer,
        ForeignKey("blood_collections.id", ondelete="CASCADE"),
        nullable=False
    )

    blood_group = Column(String(5), nullable=False)
    component_type = Column(Enum(ComponentType), nullable=False)
    storage_rack = Column(String(50), nullable=True)
    quantity_ml = Column(Integer, nullable=True)  # updated to match router logic
    expiry_date = Column(Date, nullable=False)
    is_expired = Column(Boolean, default=False)

    status = Column(Enum(BloodStatus), default=BloodStatus.PENDING_LAB, nullable=False)

    collection = relationship("BloodCollection", back_populates="inventory")
    created_at = Column(DateTime, server_default=func.now())


# ===================== BLOOD TEST REPORT =====================

class BloodTestReport(Base):
    __tablename__ = "blood_test_reports"

    id = Column(Integer, primary_key=True, index=True)

    collection_id = Column(
        Integer,
        ForeignKey("blood_collections.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    hiv = Column(Boolean, default=False)
    hbv = Column(Boolean, default=False)
    hcv = Column(Boolean, default=False)
    malaria = Column(Boolean, default=False)
    syphilis = Column(Boolean, default=False)

    eligibility = Column(Boolean, default=True)
    rejection_reason = Column(Text, nullable=True)

    tested_by = Column(Integer, nullable=True)
    test_date = Column(DateTime, server_default=func.now())

    collection = relationship("BloodCollection", back_populates="test_report")


# ===================== PATIENT =====================
#
# class Patient(Base):
#     __tablename__ = "patients"
#
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     age = Column(Integer)
#     phone = Column(String(10))
#     address = Column(String(255))
#     gender = Column(String(10))
#     blood_group = Column(String(5))
#     diagnosis = Column(String(255))
#     created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
#
#     created_at = Column(DateTime, server_default=func.now())
#     updated_at = Column(DateTime, onupdate=func.now())
#
#     blood_requests = relationship(
#         "BloodRequest",
#         back_populates="patient",
#         cascade="all, delete-orphan"
#     )


# ===================== BLOOD REQUEST =====================

class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)

    # Blood patient NEEDS
    blood_group = Column(String(5), nullable=False)

    # Blood patient CAN GIVE (for exchange)
    exchange_blood_group = Column(String(5), nullable=True)

    component_type = Column(Enum(ComponentType), nullable=False)
    units_required = Column(Integer, nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    allow_exchange = Column(Boolean, default=False)
    matched_donor_id = Column(Integer, ForeignKey("blood_donors.id"), nullable=True)

    matched_request_id = Column(Integer, ForeignKey("blood_requests.id", ondelete="SET NULL"), nullable=True)

    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    patient = relationship("Patient", back_populates="blood_requests")
    matched_request = relationship("BloodRequest", remote_side=[id])


