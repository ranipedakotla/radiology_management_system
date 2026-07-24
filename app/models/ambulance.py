import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, func,Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SqlEnum
from app.db.base import Base


class AmbulanceStatus(str, enum.Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    INACTIVE = "INACTIVE"


class AmbulanceType(str, enum.Enum):
    BLS = "BLS"
    ALS = "ALS"
    CARDIAC_AMBULANCE = "CARDIAC_AMBULANCE"
    NICA_AMBULANCE = "NICA_AMBULANCE"
    PATIENT_TRANSPORT_VEHICLE = "PATIENT_TRANSPORT_VEHICLE"
    DEAD_BODY_FREEZER_AMBULANCE = "DEAD_BODY_FREEZER_AMBULANCE"


# Booking Type Enum
class BookingType(str, enum.Enum):
    EMERGENCY = "Emergency"
    SCHEDULED = "Scheduled"


# Emergency Type Enum
class EmergencyType(str, enum.Enum):
    ACCIDENT = "Accident"
    CARDIAC = "Cardiac"
    MATERNITY = "Maternity"
    TRAUMA = "Trauma"


# Payment Mode Enum
class PaymentMode(str, enum.Enum):
    CASH = "Cash"
    CASHLESS = "Cashless"

class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(50), unique=True, nullable=False)

    ambulance_type = Column(SqlEnum(AmbulanceType))
    status = Column(SqlEnum(AmbulanceStatus), default=AmbulanceStatus.OFFLINE)

    latitude = Column(Float)
    longitude = Column(Float)
    driver = relationship(
        "Driver",
        back_populates="ambulance",
        uselist=False,
        cascade="all, delete"
    )



class Booking(Base):
    __tablename__ = "ambulance_bookings"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(String(20), unique=True, nullable=False)

    booking_datetime = Column(
        DateTime,
        server_default=func.now()
    )

    booking_type = Column(
        Enum(BookingType),
        nullable=False
    )

    caller_name = Column(String(100), nullable=False)
    caller_phone = Column(String(15), nullable=False)

    pickup_location = Column(Text, nullable=False)  # Google map address / lat-long
    drop_location = Column(Text, nullable=False)

    patient_name = Column(String(100))
    patient_age = Column(Integer)
    patient_gender = Column(String(10))  # or Enum if you want strict

    emergency_type = Column(
        Enum(EmergencyType),
        nullable=False
    )

    payment_mode = Column(
        Enum(PaymentMode),
        nullable=False
    )

    created_at = Column(DateTime, server_default=func.now())

