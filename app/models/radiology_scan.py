from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyScan(Base):
    __tablename__ = "radiology_scan"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Link with Radiology Registration
    registration_id: Mapped[int] = mapped_column(
        ForeignKey("radiology_registration.id"),
        nullable=False
    )

    technician_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    scan_status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    hold_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    reschedule_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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
