from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RadiologyScan(Base):
    __tablename__ = "radiology_scan"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Refers logically to radiology_appointment.id
    appointment_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Scan status
    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    # Technician who performs the scan
    technician_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )

    # Scan start and completion times
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
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
