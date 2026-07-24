import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy import Enum as SqlEnum
from app.db.base import Base


class PatientCondition(str, enum.Enum):
    STABLE = "STABLE"
    CRITICAL = "CRITICAL"


class ReferredBy(str, enum.Enum):
    HOSPITAL = "HOSPITAL"
    POLICE = "POLICE"
    PUBLIC = "PUBLIC"


class PatientTransport(Base):
    __tablename__ = "patient_transports"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(Integer, ForeignKey("emergency_requests.id"))

    # Patient Info
    patient_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)

    primary_contact = Column(String(15), nullable=False)
    secondary_contact = Column(String(15))

    # Locations
    pickup_location = Column(String(255), nullable=False)
    drop_location = Column(String(255), nullable=False)

    # Medical
    condition_at_pickup = Column(SqlEnum(PatientCondition))
    referred_by = Column(SqlEnum(ReferredBy))

    attendant_name = Column(String(100))

    created_at = Column(DateTime, server_default=func.now())

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(Integer, ForeignKey("emergency_requests.id"), nullable=False)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)

    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)

    distance_km = Column(Float, default=0.0)