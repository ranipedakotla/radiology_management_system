from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.pathology_tests  import SampleType


# ------ ORDERS ------
class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"))
    priority: Mapped[str] = mapped_column(String(16), default="normal")  # normal/urgent
    source: Mapped[str | None] = mapped_column(String(32))  # walk-in/opd/ipd/referral
    status: Mapped[str] = mapped_column(String(24), default="created")   # created, sample_collected, result_entered, validated, reported, cancelled
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


    patient = relationship("Patient")
    doctor = relationship("Doctor")
    items = relationship("LabOrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    reports = relationship(
        "Report",
        backref="order",
        cascade="all, delete-orphan",
        lazy="joined"  # optional; preloads reports with the order
    )


class LabOrderItem(Base):
    __tablename__ = "lab_order_items"
    __table_args__ = (UniqueConstraint("order_id", "test_id", name="uq_order_test"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id", ondelete="CASCADE"))
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    panel_id: Mapped[int | None] = mapped_column(ForeignKey("panels.id"), default=None)
    sample_id: Mapped[int | None] = mapped_column(ForeignKey("samples.id"), default=None)
    status: Mapped[str] = mapped_column(String(24), default="created")  # created, in_progress, result_entered

    order = relationship("LabOrder", back_populates="items")
    test = relationship("Test")
    sample = relationship("Sample", lazy="selectin")
    result = relationship("Result", back_populates="order_item", uselist=False, lazy="selectin")

    sample_collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sample_type_id: Mapped[int | None] = mapped_column(ForeignKey("sample_types.id", ondelete="SET NULL"), nullable=True)
    sample_type: Mapped[SampleType | None] = relationship("SampleType")


# ------ SAMPLES ------
class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    accession_no: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    sample_type_id: Mapped[int] = mapped_column(ForeignKey("sample_types.id"))
    collected_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    remarks: Mapped[str | None] = mapped_column(String(255))


# # ------ RESULTS ------
# class Result(Base):
#     __tablename__ = "results"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     order_item_id: Mapped[int] = mapped_column(ForeignKey("lab_order_items.id", ondelete="CASCADE"), unique=True)
#     test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
#     status: Mapped[str] = mapped_column(String(24), default="entered")  # entered, validated
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#     # test_interpretation: Mapped[str | None] = mapped_column(String(1024), nullable=True)
#     # test_note: Mapped[str | None] = mapped_column(String(1024), nullable=True)
#     test_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
#     test_note: Mapped[str | None] = mapped_column(Text, nullable=True)
#     entered_by: Mapped[int | None] = mapped_column(
#         ForeignKey("users.id", ondelete="SET NULL"), nullable=True
#     )
#     validated_by: Mapped[int | None] = mapped_column(
#         ForeignKey("users.id", ondelete="SET NULL"), nullable=True
#     )
#
#     order_item = relationship("LabOrderItem", back_populates="result")
#     values = relationship("ResultValue", back_populates="result", cascade="all, delete-orphan", lazy="selectin")
#     entered_by_user: Mapped["User"] = relationship(
#         "User", foreign_keys=[entered_by], lazy="selectin"
#     )
#     validated_by_user: Mapped["User"] = relationship(
#         "User", foreign_keys=[validated_by], lazy="selectin"
#     )
#     values: Mapped[list["ResultValue"]] = relationship(
#         "ResultValue",
#         back_populates="result",
#         cascade="all, delete-orphan",
#         lazy="selectin",
#     )
#
# class ResultValue(Base):
#     __tablename__ = "result_values"
#
#     id: Mapped[int] = mapped_column(primary_key=True)
#     result_id: Mapped[int] = mapped_column(ForeignKey("results.id", ondelete="CASCADE"))
#     analyte_id: Mapped[int] = mapped_column(ForeignKey("analytes.id"))
#     value_text: Mapped[str | None] = mapped_column(String(64))
#     value_num: Mapped[float | None] = mapped_column(Float)
#     flag: Mapped[str] = mapped_column(String(4), default="N")  # N, L, H, etc.
#     measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#     interpretation: Mapped[str | None] = mapped_column(String(255), nullable=True)
#     note: Mapped[str | None] = mapped_column(String(255), nullable=True)
#
#     result = relationship("Result", back_populates="values")
#     analyte: Mapped["Analyte"] = relationship("Analyte", lazy="selectin")

class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("lab_order_items.id", ondelete="CASCADE"), unique=True
    )
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    status: Mapped[str] = mapped_column(String(24), default="entered")  # entered, validated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # per-test comments/summary for the result
    test_interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    entered_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    order_item: Mapped["LabOrderItem"] = relationship("LabOrderItem", back_populates="result")
    values: Mapped[list["ResultValue"]] = relationship(
        "ResultValue",
        back_populates="result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    entered_by_user: Mapped["User"] = relationship("User", foreign_keys=[entered_by], lazy="selectin")
    validated_by_user: Mapped["User"] = relationship("User", foreign_keys=[validated_by], lazy="selectin")


class ResultValue(Base):
    __tablename__ = "result_values"
    __table_args__ = (
        # strongly recommended to prevent duplicates per analyte in a result
        UniqueConstraint("result_id", "analyte_id", name="uq_result_analyte"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("results.id", ondelete="CASCADE"))
    analyte_id: Mapped[int] = mapped_column(ForeignKey("analytes.id"))

    value_text: Mapped[str | None] = mapped_column(String(64))
    value_num: Mapped[float | None] = mapped_column(Float)
    flag: Mapped[str] = mapped_column(String(4), default="N")  # N, L, H, …
    measured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    interpretation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    result: Mapped["Result"] = relationship("Result", back_populates="values")
    analyte: Mapped["Analyte"] = relationship("Analyte", lazy="selectin")


class Validation(Base):
    __tablename__ = "validations"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("results.id", ondelete="CASCADE"), unique=True)
    validated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    validated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    comments: Mapped[str | None] = mapped_column(String(255))


# ------ REPORTS (stub for now; PDF/QR/S3 next step) ------
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("lab_orders.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    s3_key: Mapped[str | None] = mapped_column(String(255))
    pdf_url: Mapped[str | None] = mapped_column(String(255))
    qr_code_token: Mapped[str | None] = mapped_column(String(64))
