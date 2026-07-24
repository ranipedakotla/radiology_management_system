from __future__ import annotations
from datetime import date, time
from sqlalchemy import ForeignKey, String, Integer, Date, UniqueConstraint, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, DateTime
from datetime import datetime
from app.db.base import Base
from app.models._mixins import TenantedMixin
from app.models.blood_bank import BloodRequest
from app.models.opd import Prescription


class Patient(Base, TenantedMixin):
    __tablename__ = "patients"

    __table_args__ = (
        UniqueConstraint("hospital_id", "patient_uid", name="uq_patients_hosp_uid"),
        UniqueConstraint("branch_id", "patient_code", name="uq_patients_branch_code"),
        UniqueConstraint("hospital_id", "aadhaar_no", name="uq_patients_hosp_aadhaar"),  # NEW
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    dob: Mapped[date | None] = mapped_column(Date)

    phone_number: Mapped[str] = mapped_column(String(20), default="")  # existing

    # NEW FIELDS
    guardian_name: Mapped[str | None] = mapped_column(String(120))
    gender: Mapped[str | None] = mapped_column(String(10))              # "Male"/"Female"/"Other"
    age: Mapped[int | None] = mapped_column(Integer)
    blood_group: Mapped[str | None] = mapped_column(String(3))          # e.g., "A+"
    marital_status: Mapped[str | None] = mapped_column(String(12))      # Single/Married/...
    email: Mapped[str | None] = mapped_column(String(120))
    location: Mapped[str | None] = mapped_column(String(200))
    diagnosis: Mapped[str | None] = mapped_column(String(255))
    reason: Mapped[str | None] = mapped_column(Text)
    aadhaar_no: Mapped[str | None] = mapped_column(String(20), index=True)
    aadhaar_file_path: Mapped[str | None] = mapped_column(String(300))  # stored in /static/...
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        onupdate=func.now(),
    )

    patient_uid: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    patient_code: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")  # type: ignore

    prescriptions: Mapped[list["Prescription"]] = relationship(
        "Prescription",
        back_populates="patient"
    )
    blood_requests: Mapped[list["BloodRequest"]] = relationship(
        "BloodRequest",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


import enum
from datetime import date, datetime

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Enum as SqlEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# ---------------- ENUMS ---------------- #

class GenderEnum(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class ShiftTypeEnum(str, enum.Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"
    NIGHT = "NIGHT"
    FLEXIBLE = "FLEXIBLE"


class AccountTypeEnum(str, enum.Enum):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"


# ---------------- MODEL ---------------- #

class Staff(Base, TenantedMixin):
    __tablename__ = "staff"


    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Basic Identity
    employee_id: Mapped[str] = mapped_column(String(20),unique=True,nullable=False)
    staff_code: Mapped[str | None] = mapped_column(String(20),index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"),nullable=True)
    # Name
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(80),nullable=True)
    full_name: Mapped[str] = mapped_column(String(150),nullable=False)
    # Contact
    email: Mapped[str] = mapped_column(String(254),unique=True,nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20),nullable=False)
    emergency_contact_name: Mapped[str] = mapped_column(String(150),nullable=False)
    emergency_contact_number: Mapped[str] = mapped_column(String(20),nullable=False)
    # Personal Info
    gender: Mapped[GenderEnum] = mapped_column(SqlEnum(GenderEnum))
    date_of_birth: Mapped[date] = mapped_column(Date,nullable=False)

    # Address
    address_street: Mapped[str | None] = mapped_column(String(255))
    address_city: Mapped[str] = mapped_column(String(100),nullable=False)
    address_state: Mapped[str] = mapped_column(String(100),nullable=False)
    address_pincode: Mapped[str] = mapped_column(String(10),nullable=False)
    address_country: Mapped[str] = mapped_column(String(100),default="India")
    # Employment
    department: Mapped[str] = mapped_column(String(100),nullable=False)

    designation: Mapped[str] = mapped_column(String(150),nullable=False)

    joining_date: Mapped[date] = mapped_column(Date,nullable=False)

    role: Mapped[str] = mapped_column(String(50),default="EMPLOYEE")

    # Qualification
    qualification: Mapped[str] = mapped_column(String(200),nullable=False)
    experience_years: Mapped[float] = mapped_column(Float,default=0.0)

    # Shift
    # shift_type: Mapped[ShiftTypeEnum] = mapped_column(SqlEnum(ShiftTypeEnum))
    shift_type: Mapped[ShiftTypeEnum] = mapped_column(
        SqlEnum(ShiftTypeEnum),
        default=ShiftTypeEnum.FLEXIBLE,
        nullable=False
    )

    shift_start: Mapped[str | None] = mapped_column(String(8))
    shift_end: Mapped[str | None] = mapped_column(String(8))

    # Salary
    monthly_salary: Mapped[float] = mapped_column(Float,nullable=False)
    # Government IDs
    pan_number: Mapped[str] = mapped_column(String(10), unique=True,nullable=False)
    aadhar_number: Mapped[str] = mapped_column(String(12),unique=True,nullable=False)
    uan_number: Mapped[str | None] = mapped_column(String(12))
    esi_number: Mapped[str | None] = mapped_column(String(17))
    # Bank Details
    bank_account_holder_name: Mapped[str] = mapped_column(String(150),nullable=False)
    bank_account_number: Mapped[str] = mapped_column(String(18),nullable=False)
    bank_ifsc_code: Mapped[str] = mapped_column(String(11),nullable=False)
    bank_name: Mapped[str] = mapped_column(String(150),nullable=False)
    bank_branch_name: Mapped[str | None] = mapped_column(String(150))
    bank_account_type: Mapped[AccountTypeEnum] = mapped_column(SqlEnum(AccountTypeEnum),default=AccountTypeEnum.SAVINGS)

    # Documents
    id_proof_url: Mapped[str | None] = mapped_column(String(500))
    id_proof_filename: Mapped[str | None] = mapped_column(String(255))
    id_proof_type: Mapped[str | None] = mapped_column(String(50))
    id_proof_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    address_proof_url: Mapped[str | None] = mapped_column(String(500))
    address_proof_filename: Mapped[str | None] = mapped_column(String(255))
    address_proof_type: Mapped[str | None] = mapped_column(String(50))
    address_proof_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    educational_certificates_urls: Mapped[str | None] = mapped_column(String(2000))
    educational_certificates_filenames: Mapped[str | None] = mapped_column(String(2000))
    experience_letters_urls: Mapped[str | None] = mapped_column(String(2000))
    experience_letters_filenames: Mapped[str | None] = mapped_column(String(2000))
    profile_photo_url: Mapped[str | None] = mapped_column(String(500))
    profile_photo_filename: Mapped[str | None] = mapped_column(String(255))
    profile_photo_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    signature_url: Mapped[str | None] = mapped_column(String(500))
    signature_filename: Mapped[str | None] = mapped_column(String(255))
    signature_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())
    # Relationships
    doctor: Mapped["Doctor | None"] = relationship(back_populates="staff",uselist=False)
    # Constraints
    __table_args__ = (UniqueConstraint("branch_id","staff_code",name="uq_staff_branch_code"),)

#
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

class Doctor(Base, TenantedMixin):
    __tablename__ = "doctors"

    __table_args__ = (
        UniqueConstraint("staff_id", name="uq_doctors_staff_id"),
        UniqueConstraint("branch_id", "doctor_code", name="uq_doctors_branch_code"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), index=True)
    consultation_fee: Mapped[int] = mapped_column(Integer, default=0)
    specialty: Mapped[str] = mapped_column(String(80), default="")
    # Doctor code
    doctor_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    # added
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # shift_start: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # shift_end: Mapped[str | None] = mapped_column(String(8), nullable=True)
    shift_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    shift_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    department:Mapped[str] = mapped_column(String(100), nullable=True)
    pan:Mapped[str] = mapped_column(String(100), nullable=True)
    aadhar:Mapped[str] = mapped_column(String(100), nullable=True)
    bank:Mapped[str] = mapped_column(String(100), nullable=True)
    account_no: Mapped[str] = mapped_column(String(100), nullable=True)
    ifsc: Mapped[str] = mapped_column(String(100), nullable=True)
    floor_location: Mapped[str] = mapped_column(String(100), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    # S3 file URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    license_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_pic_url:Mapped[Optional[str]]=mapped_column(String(500), nullable=True)
    staff: Mapped["Staff"] = relationship(back_populates="doctor")

class PatientBranchCode(Base):
    __tablename__ = "patient_branch_codes"
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), primary_key=True)
    branch_id:  Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
    code:       Mapped[str] = mapped_column(String(20))
    Patient.branch_codes: Mapped[list["PatientBranchCode"]] = relationship(
        "PatientBranchCode", cascade="all, delete-orphan", lazy="selectin"
    )

class StaffBranch(Base):
    __tablename__ = "staff_branches"
    staff_id:  Mapped[int] = mapped_column(ForeignKey("staff.id"), primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
    Staff.branches: Mapped[list["StaffBranch"]] = relationship(
        "StaffBranch", cascade="all, delete-orphan", lazy="selectin"
    )


class DoctorBranch(Base):
    __tablename__ = "doctor_branches"
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
    Doctor.branches: Mapped[list["DoctorBranch"]] = relationship(
        "DoctorBranch", cascade="all, delete-orphan", lazy="selectin"
    )