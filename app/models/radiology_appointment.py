from datetime import date, time, datetime

from sqlalchemy import Date, Time, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyAppointment(Base):
    __tablename__ = "radiology_appointment"

    # Auto-generated appointment ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Existing radiology registration ID
    radiology_registration_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Selected lab test ID
    lab_test_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Appointment date
    appointment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # Appointment time
    appointment_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    # Appointment status
    status: Mapped[str] = mapped_column(
        String(30),
        default="Scheduled",
        nullable=False
    )

    # Optional remarks
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Created timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Updated timestamp
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True
    )