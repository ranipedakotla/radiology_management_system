from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyRegistration(Base):
    __tablename__ = "radiology_registration"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Existing hospital patient ID
    # Used for OPD/IPD patient
    patient_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # External patient ID
    # Used when patient is not already registered in HMS
    external_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Radiology test details
    test_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    test_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Doctor details
    doctor_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    # Registration status
    status: Mapped[str] = mapped_column(
        String(30),
        default="Registered",
        nullable=False
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
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