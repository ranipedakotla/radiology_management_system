import enum
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import relationship

from app.db.base import Base


class DriverStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BUSY = "BUSY"


class IDProofType(str, enum.Enum):
    AADHAAR = "Aadhaar"
    PASSPORT = "Passport"
    VOTER_ID = "Voter ID"


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String(20), unique=True, nullable=False)

    driver_name = Column(String(100), nullable=False)

    id_proof_type = Column(
        SqlEnum(
            IDProofType,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        nullable=False
    )
    id_proof_number = Column(String(50), nullable=False)

    driver_photo = Column(String(255))

    license_number = Column(String(50), unique=True, nullable=False)
    license_validity_date = Column(Date, nullable=False)

    primary_phone = Column(String(15), nullable=False)
    secondary_phone = Column(String(15))

    address = Column(Text, nullable=False)

    experience_years = Column(Integer, default=0)

    active_status = Column(
        SqlEnum(
            DriverStatus,
            values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        default=DriverStatus.ACTIVE
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    ambulance_id = Column(Integer, ForeignKey("ambulances.id"))

    ambulance = relationship("Ambulance", back_populates="driver")

