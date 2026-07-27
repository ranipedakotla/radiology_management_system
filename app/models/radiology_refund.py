from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyRefund(Base):
    __tablename__ = "radiology_refunds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Logical reference to Radiology Registration
    registration_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Refund amount
    refund_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Reason for refund
    refund_reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Refund status
    status: Mapped[str] = mapped_column(
        String(30),
        default="Pending",
        nullable=False
    )

    # Additional remarks
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