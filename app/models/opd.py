from datetime import datetime, date
from sqlalchemy import ForeignKey, String, Integer, Float, Boolean, Text, DateTime, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TenantedMixin

class OPDVisit(Base, TenantedMixin):
    __tablename__ = "opd_visits"

    __table_args__ = (UniqueConstraint("branch_id", "visit_id", name="uq_opd_branch_visitno"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True, index=True)

    visit_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # ward_name: Mapped[str] = mapped_column(String(100))
    chief_complaint: Mapped[str | None] = mapped_column(Text)
    symptoms: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    blood_sugar_bf: Mapped[float | None] = mapped_column(nullable=True)
    blood_sugar_af: Mapped[float | None] = mapped_column(nullable=True)

    height_cm: Mapped[int | None]
    weight_kg: Mapped[float | None]
    temp_c: Mapped[float | None]
    bp_systolic: Mapped[int | None]
    bp_diastolic: Mapped[int | None]
    pulse: Mapped[int | None]
    resp_rate: Mapped[int | None]
    spo2: Mapped[int | None]

    diagnoses: Mapped[list["OPDVisitDiagnosis"]] = relationship(back_populates="visit", cascade="all, delete-orphan")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="visit", cascade="all, delete-orphan")
    lab_tests: Mapped[list["OpdVisitLabTest"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
        order_by="OpdVisitLabTest.id.asc()",
    )


class OPDVisitDiagnosis(Base):
    __tablename__ = "opd_visit_diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("opd_visits.id"), index=True)
    icd_code: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    visit: Mapped[OPDVisit] = relationship(back_populates="diagnoses")

#
# class Prescription(Base):
#     __tablename__ = "prescriptions"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     visit_id: Mapped[int] = mapped_column(ForeignKey("opd_visits.id"), index=True)
#     prescribed_by_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#     notes: Mapped[str | None] = mapped_column(Text)
#
#     visit: Mapped[OPDVisit] = relationship(back_populates="prescriptions")
#     items: Mapped[list["PrescriptionItem"]] = relationship(back_populates="prescription", cascade="all, delete-orphan")

class Prescription(Base):
    __tablename__ = "prescriptions"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Multi-tenant
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("hospitals.id"),
        index=True,
    )

    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id"),
        index=True,
    )

    # OPD / Visit Context
    visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("opd_visits.id"),
        index=True,
        nullable=True,
    )

    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.id"),
        nullable=True,
    )

    prescribed_by_staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"),
        nullable=True,
    )

    pharmacist_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    # Doctor Details
    doctor_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    doctor_reg_no: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    registration_no: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    prescription_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Clinical Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Prescription File/Image
    image_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    visit = relationship(
        "OPDVisit",
        back_populates="prescriptions",
    )

    patient = relationship(
        "Patient",
        back_populates="prescriptions",
    )

    prescribed_by_staff = relationship(
        "Staff",
        foreign_keys=[prescribed_by_staff_id],
    )

    pharmacist = relationship(
        "User",
        foreign_keys=[pharmacist_id],
    )

    items = relationship(
        "PrescriptionItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
    )

    hospital = relationship(
        "Hospital",
        foreign_keys=[hospital_id],
    )

    branch = relationship(
        "Branch",
        foreign_keys=[branch_id],
    )

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), index=True)
    drug_name: Mapped[str] = mapped_column(String(120))
    dose: Mapped[str | None] = mapped_column(String(60))
    frequency: Mapped[str | None] = mapped_column(String(60))
    duration: Mapped[str | None] = mapped_column(String(60))
    route: Mapped[str | None] = mapped_column(String(40))
    instructions: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[int | None]
    unit: Mapped[str | None] = mapped_column(String(20))

    prescription: Mapped[Prescription] = relationship(back_populates="items")

class OpdVisitLabTest(Base):
    __tablename__ = "opd_visit_lab_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("opd_visits.id", ondelete="CASCADE"), index=True)
    test_name: Mapped[str] = mapped_column(String(120))
    test_code: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(String(20), default="Routine")  # Routine | Urgent | Stat
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="prescribed")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    # IMPORTANT: class name must match exactly -> OPDVisit
    visit: Mapped["OPDVisit"] = relationship(back_populates="lab_tests")