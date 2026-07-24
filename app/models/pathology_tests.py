from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))


class SampleType(Base):
    __tablename__ = "sample_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class Test(Base):
    __tablename__ = "tests"
    __table_args__ = (UniqueConstraint("code", name="uq_tests_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    method: Mapped[str | None] = mapped_column(String(64))
    sample_type_id: Mapped[int] = mapped_column(ForeignKey("sample_types.id"))
    category: Mapped[str | None] = mapped_column(String(64))
    tat_hours: Mapped[int] = mapped_column(Integer, default=24)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    sample_type = relationship("SampleType")
    analytes = relationship("Analyte", back_populates="test", cascade="all, delete-orphan", lazy="selectin")


# class Analyte(Base):
#     __tablename__ = "analytes"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
#     code: Mapped[str] = mapped_column(String(32))
#     name: Mapped[str] = mapped_column(String(128))
#     unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"))
#     is_calculated: Mapped[bool] = mapped_column(Boolean, default=False)
#     formula: Mapped[str | None] = mapped_column(String(256))
#     unit: Mapped["Unit | None"] = relationship("Unit", lazy="selectin")
#
#     test = relationship("Test", back_populates="analytes")
#     unit = relationship("Unit")
#     ranges = relationship("ReferenceRange", back_populates="analyte", cascade="all, delete-orphan", lazy="selectin")
#

class Analyte(Base):
    __tablename__ = "analytes"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(128))
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"), nullable=True)
    is_calculated: Mapped[bool] = mapped_column(Boolean, default=False)
    formula: Mapped[str | None] = mapped_column(String(256))

    test: Mapped["Test"] = relationship("Test", back_populates="analytes")
    unit: Mapped["Unit | None"] = relationship("Unit", lazy="selectin")   # <-- keep only this one
    ranges: Mapped[list["ReferenceRange"]] = relationship(
        "ReferenceRange", back_populates="analyte", cascade="all, delete-orphan", lazy="selectin"
    )

class ReferenceRange(Base):
    __tablename__ = "reference_ranges"
    id: Mapped[int] = mapped_column(primary_key=True)
    analyte_id: Mapped[int] = mapped_column(ForeignKey("analytes.id"))
    sex: Mapped[str | None] = mapped_column(String(1))  # 'M','F','O' or None
    age_min_days: Mapped[int] = mapped_column(Integer, default=0)
    age_max_days: Mapped[int] = mapped_column(Integer, default=365000)
    low: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String(256))

    analyte = relationship("Analyte", back_populates="ranges")


class Panel(Base):
    __tablename__ = "panels"
    __table_args__ = (UniqueConstraint("code", name="uq_panels_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items = relationship("PanelItem", back_populates="panel", cascade="all, delete-orphan", lazy="selectin")


class PanelItem(Base):
    __tablename__ = "panel_items"
    __table_args__ = (UniqueConstraint("panel_id", "test_id", name="uq_panel_test"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id", ondelete="CASCADE"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"))

    panel = relationship("Panel", back_populates="items")
    test = relationship("Test")
