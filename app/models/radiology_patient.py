from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyPatient(Base):
    __tablename__ = "radiology_patient"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    first_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False
    )

    last_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    dob: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    guardian_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    gender: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    age: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    marital_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    diagnosis: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    aadhaar_no: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    aadhaar_file_path: Mapped[str | None] = mapped_column(
        String(300),
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