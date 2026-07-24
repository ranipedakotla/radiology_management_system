from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column


class TenantedMixin:
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.id"), index=True)
    branch_id:  Mapped[int] = mapped_column(ForeignKey("branches.id"),  index=True)
