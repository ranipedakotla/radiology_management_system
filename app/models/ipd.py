# app/models/ipd.py
from datetime import datetime
from sqlalchemy import (
    String, Text, ForeignKey, Boolean, DateTime, Integer,UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

from app.models._mixins import TenantedMixin


# ---------------------------
# Master data
# ---------------------------

class Floor(Base, TenantedMixin):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("branch_id", "name", name="uq_floor_branch_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    groups: Mapped[list["BedGroup"]] = relationship(
        back_populates="floor", cascade="all, delete-orphan"
    )

class BedType(Base,TenantedMixin):
    __tablename__ = "bed_types"
    __table_args__ = (UniqueConstraint("branch_id", "name", name="uq_bedtype_branch_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    beds: Mapped[list["Bed"]] = relationship(back_populates="bed_type")

class BedGroup(Base, TenantedMixin):
    __tablename__ = "bed_groups"
    __table_args__ = (UniqueConstraint("branch_id", "name", name="uq_bedgroup_branch_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id"), index=True)
    floor: Mapped["Floor"] = relationship(back_populates="groups")
    beds: Mapped[list["Bed"]] = relationship(
        back_populates="bed_group", cascade="all, delete-orphan"
    )

class Bed(Base, TenantedMixin):
    __tablename__ = "beds"
    __table_args__ = (UniqueConstraint("branch_id", "code", name="uq_bed_branch_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # e.g. "GF - 101"
    bed_type_id: Mapped[int] = mapped_column(ForeignKey("bed_types.id"), index=True)
    bed_group_id: Mapped[int] = mapped_column(ForeignKey("bed_groups.id"), index=True)
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False)

    bed_type: Mapped["BedType"] = relationship(back_populates="beds")
    bed_group: Mapped["BedGroup"] = relationship(back_populates="beds")

    # optional backrefs from admissions/transfers
    current_admissions: Mapped[list["IPDAdmission"]] = relationship(
        back_populates="bed", cascade="save-update", primaryjoin="Bed.id==IPDAdmission.bed_id"
    )


class IPDAdmission(Base, TenantedMixin):
    __tablename__ = "ipd_admissions"

    __table_args__ = (UniqueConstraint("branch_id", "admission_no", name="uq_ipd_branch_admno"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    admission_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # varchar(32) in DB

    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), index=True)

    admit_datetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str | None] = mapped_column(Text)

    # snapshot columns present in your table
    current_ward: Mapped[str | None] = mapped_column(String(60))
    current_room: Mapped[str | None] = mapped_column(String(30))
    current_bed: Mapped[str | None] = mapped_column(String(30))

    status: Mapped[str] = mapped_column(String(20), index=True, default="admitted")
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    bed: Mapped["Bed"] = relationship(back_populates="current_admissions")
    transfers: Mapped[list["IPDTransfer"]] = relationship(back_populates="admission", cascade="all, delete-orphan")
    discharge: Mapped["IPDDischarge | None"] = relationship(back_populates="admission", uselist=False, cascade="all, delete-orphan")




class IPDTransfer(Base, TenantedMixin):
    __tablename__ = "ipd_transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("ipd_admissions.id"), index=True)

    from_bed_id: Mapped[int | None] = mapped_column(ForeignKey("beds.id"), nullable=True, index=True)
    to_bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), index=True)

    transfer_datetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str | None] = mapped_column(Text)

    admission: Mapped["IPDAdmission"] = relationship(back_populates="transfers")
    from_bed: Mapped["Bed | None"] = relationship(foreign_keys=[from_bed_id])
    to_bed: Mapped["Bed"] = relationship(foreign_keys=[to_bed_id])

class IPDDischarge(Base, TenantedMixin):
    __tablename__ = "ipd_discharges"

    id: Mapped[int] = mapped_column(primary_key=True)
    admission_id: Mapped[int] = mapped_column(
        ForeignKey("ipd_admissions.id"), index=True, unique=True
    )
    discharge_datetime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    outcome: Mapped[str] = mapped_column(String(30), default="recovered")  # recovered | LAMA | deceased | referral
    notes: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    advice: Mapped[str | None] = mapped_column(Text)
    # created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)


    admission: Mapped["IPDAdmission"] = relationship(back_populates="discharge")



class BedOccupancy(Base, TenantedMixin):
    __tablename__ = "bed_occupancies"
    id: Mapped[int] = mapped_column(primary_key=True)
    admission_id: Mapped[int] = mapped_column(ForeignKey("ipd_admissions.id", ondelete="CASCADE"), index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), index=True)
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end: Mapped[datetime | None] = mapped_column(DateTime)

    bed: Mapped["Bed"] = relationship("Bed")
    admission: Mapped["IPDAdmission"] = relationship("IPDAdmission")
