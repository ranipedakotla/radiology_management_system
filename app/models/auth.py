from __future__ import annotations
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import ForeignKey, UniqueConstraint, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

# ---------- association tables (ONLY these; no mapped classes for them) ----------
user_roles = sa.Table(
    "user_roles",
    Base.metadata,
    sa.Column("user_id", sa.Integer, ForeignKey("users.id"), primary_key=True),
    sa.Column("role_id", sa.Integer, ForeignKey("roles.id"), primary_key=True),
)

role_permissions = sa.Table(
    "role_permissions",
    Base.metadata,
    sa.Column("role_id", sa.Integer, ForeignKey("roles.id"), primary_key=True),
    sa.Column("permission_id", sa.Integer, ForeignKey("permissions.id"), primary_key=True),
)

# ----------------------------------- models -------------------------------------
# class User(Base):
#     __tablename__ = "users"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     email: Mapped[str] = mapped_column(sa.String(120), unique=True, index=True)
#     phone: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
#     password_hash: Mapped[str] = mapped_column(sa.String(255))
#     is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True)
#     last_login_at: Mapped[datetime | None] = mapped_column(sa.DateTime, nullable=True)  # <-- Python datetime
#
#     # tenant context
#     hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), index=True, nullable=True)
#     current_branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"), index=True, nullable=True)
#
#     hospital = relationship("Hospital", back_populates="users", foreign_keys=[hospital_id])
#     current_branch = relationship("Branch", back_populates="users", foreign_keys=[current_branch_id])
#
#     roles = relationship("Role", secondary=user_roles, back_populates="users")


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Authentication
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Authorization
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    active_session_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        onupdate=func.now(),
    )

    # Multi-tenant / Hospital Context
    hospital_id: Mapped[int] = mapped_column(
        ForeignKey("hospitals.id"),
        index=True,
        nullable=False,
    )

    current_branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id"),
        index=True,
        nullable=False,
    )

    # Relationships
    hospital = relationship(
        "Hospital",
        back_populates="users",
        foreign_keys=[hospital_id],
    )

    current_branch = relationship(
        "Branch",
        back_populates="users",
        foreign_keys=[current_branch_id],
    )

    # RBAC (if using role table)
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )

    # Pharmacy-related relationships
    assigned_shifts = relationship(
        "UserShift",
        back_populates="user",
    )

    sales = relationship(
        "Sale",
        back_populates="pharmacist",
    )

    shifts = relationship(
        "ShiftLog",
        back_populates="pharmacist",
        foreign_keys="ShiftLog.pharmacist_id",
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), unique=True, index=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(sa.String(120))

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# Optional helper table for branch access. This is fine to keep as a mapped class
# because there is NO separate sa.Table for it elsewhere.

class UserBranch(Base):
    __tablename__ = "user_branches"
    __table_args__ = (UniqueConstraint("user_id", "branch_id", name="uq_user_branch"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), primary_key=True)
