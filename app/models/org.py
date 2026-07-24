from typing import TYPE_CHECKING,Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from sqlalchemy import Column,String, Boolean, Float, ForeignKey

if TYPE_CHECKING:  # only for type hints; avoids import cycles at runtime
    from app.models.auth import User

class Hospital(Base):
    __tablename__ = "hospitals"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(default=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    emergency_available: Mapped[bool] = mapped_column(Boolean, default=True)
    branches = relationship("Branch", back_populates="hospital")
    departments = relationship("Department", back_populates="hospital")
    # NEW: reverse side of User.hospital
    users = relationship(
        "User",                      # type: ignore[name-defined]
        back_populates="hospital",
        foreign_keys="User.hospital_id",
    )


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    location:Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    contact_number:Mapped[int]

    hospital = relationship("Hospital", back_populates="branches")
    # NEW: reverse side of User.current_branch
    users = relationship(
        "User",                      # type: ignore[name-defined]
        back_populates="current_branch",
        foreign_keys="User.current_branch_id",
    )
    departments = relationship("Department", back_populates="branch")


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("hospitals.id"),
        index=True
    )

    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id"),
        index=True
    )

    hospital = relationship(
        "Hospital",
        back_populates="departments"
    )

    branch = relationship(
        "Branch",
        back_populates="departments"
    )
