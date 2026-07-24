from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from datetime import time,date
from app.models._mixins import TenantedMixin

class DoctorSchedule(Base, TenantedMixin):
    __tablename__ = "doctor_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    # day_of_week: Mapped[int]
    schedule_date: Mapped[date]
    start_time: Mapped[time]
    end_time: Mapped[time]
    slot_minutes: Mapped[int] = mapped_column(default=15)
    max_patients: Mapped[int] = mapped_column(default=0)
    hospital_id: Mapped[int] = mapped_column(default=0)
    branch_id: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        UniqueConstraint("branch_id", "doctor_id", "schedule_date", "start_time", "end_time",
                            name="uq_doc_day_window_branch"),
    )

