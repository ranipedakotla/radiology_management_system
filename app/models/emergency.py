import enum
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SqlEnum

from app.db.base import Base


class EmergencyType(str, enum.Enum):
    ACCIDENT = "ACCIDENT"
    CARDIAC = "CARDIAC"
    TRAUMA = "TRAUMA"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    START_PICKUP = "START_PICKUP"
    PICKED_UP = "PICKED_UP"
    TRANSPORTING = "TRANSPORTING"
    DROPPED = "DROPPED"
    COMPLETED = "COMPLETED"


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String(50), nullable=False)
    contact = Column(String(10), nullable=False)

    pickup_location = Column(String(255), nullable=False)
    drop_location = Column(String(255))

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    emergency_type = Column(SqlEnum(EmergencyType))
    status = Column(SqlEnum(RequestStatus), default=RequestStatus.PENDING)

    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"))

    ambulance = relationship("Ambulance")

    created_at = Column(DateTime(timezone=True), server_default=func.now())