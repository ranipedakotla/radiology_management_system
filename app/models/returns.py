from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Float,
    JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.org import Branch


from app.db.base import Base

class ReturnType(enum.Enum):
    REFUND = "REFUND"
    REPLACEMENT = "REPLACEMENT"


class Return(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    hospital_id = Column(
        Integer,
        ForeignKey("hospitals.id"),
        nullable=False,
        index=True
    )

    branch_id = Column(
        Integer,
        ForeignKey("branches.id"),
        nullable=False,
        index=True
    )


    # Reference sale
    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        nullable=False
    )

    return_type = Column(
        Enum(ReturnType),
        nullable=False
    )

    reason = Column(String(255), nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    items = relationship(
        "ReturnItem",
        back_populates="return_ref",
        cascade="all, delete-orphan"
    )

    refund = relationship(
        "Refund",
        back_populates="return_ref",
        uselist=False,
        cascade="all, delete-orphan"
    )

    sale = relationship("Sale")
    hospital = relationship("Hospital")
    branches = relationship("Branch")



class ReturnItem(Base):
    __tablename__ = "return_items"

    id = Column(Integer, primary_key=True, index=True)

    return_id = Column(
        Integer,
        ForeignKey("returns.id", ondelete="CASCADE")
    )

    sale_item_id = Column(
        Integer,
        ForeignKey("sale_items.id"),
        nullable=False
    )

    batch_id = Column(
        Integer,
        ForeignKey("batches.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False)


    return_ref = relationship(
        "Return",
        back_populates="items"
    )

    sale_item = relationship("SaleItem")
    batch = relationship("Batch")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)

    return_id = Column(
        Integer,
        ForeignKey("returns.id", ondelete="CASCADE"),
        unique=True
    )

    amount = Column(Float, nullable=False)

    # cash / upi / card
    refund_mode = Column(String(20), nullable=False)

    # Cash audit tracking
    denominations = Column(JSON, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    return_ref = relationship(
        "Return",
        back_populates="refund"
    )