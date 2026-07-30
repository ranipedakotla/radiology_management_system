from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RadiologyRefund(Base):
    __tablename__ = "radiology_refund"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Linked Radiology Registration
    registration_id: Mapped[int] = mapped_column(
        ForeignKey("radiology_registration.id"),
        nullable=False
    )

    # Cancellation Reason
    cancellation_reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Refund Amount
    refund_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Pending / Approved / Rejected
    approval_status: Mapped[str] = mapped_column(
        String(20),
        default="Pending",
        nullable=False
    )

    # Cash / UPI / Card / Bank Transfer
    refund_mode: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    # Pending / Refunded / Closed
    refund_status: Mapped[str] = mapped_column(
        String(20),
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