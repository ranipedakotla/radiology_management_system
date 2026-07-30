from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyRegistration(Base):
    __tablename__ = "radiology_registration"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Radiology Registration ID
    registration_id: Mapped[str | None] = mapped_column(
        String(30),
        unique=True,
        nullable=True
    )

    # Existing HMS Patient
    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.id"),
        nullable=True
    )

    # Manual Radiology Patient
    external_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Test Details
    test_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    test_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Referring Doctor
    doctor_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    # Registration Status
    status: Mapped[str] = mapped_column(
        String(30),
        default="Booked",
        nullable=False
    )

    # Scan Status
    scan_status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True
    )