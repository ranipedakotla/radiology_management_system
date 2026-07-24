from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AmbulanceInvoice(Base):
    __tablename__ = "ambulance_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(String, unique=True, index=True)  # e.g. INV-1001

    patient_name = Column(String)
    patient_age = Column(Integer)
    patient_gender = Column(String)
    patient_contact = Column(String)

    booking_person = Column(String)
    pickup_address = Column(String)
    drop_address = Column(String)

    ambulance_type = Column(String)
    vehicle_number = Column(String)
    driver_name = Column(String)

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    distance = Column(Float)

    subtotal = Column(Float)
    tax_percent = Column(Float)
    tax_amount = Column(Float)
    discount_amount = Column(Float)
    grand_total = Column(Float)

    payment_status = Column(String)
    payment_method = Column(String)
    transaction_id = Column(String)

    file_key = Column(String(300), nullable=True)
