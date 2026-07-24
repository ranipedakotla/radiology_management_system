from pydantic import BaseModel, model_validator
from datetime import datetime

class Charges(BaseModel):
    base_fare_qty: int
    base_fare_unit: float

    distance_qty: float
    distance_unit: float

    waiting_qty: float
    waiting_unit: float

    oxygen_qty: int
    oxygen_unit: float

    emergency_qty: int
    emergency_unit: float

    night_qty: int
    night_unit: float

    # Computed fields (not input)
    base_fare_total: float = 0
    distance_total: float = 0
    waiting_total: float = 0
    oxygen_total: float = 0
    emergency_total: float = 0
    night_total: float = 0

    subtotal: float = 0

    @model_validator(mode="after")
    def calculate(self):
        base = self.base_fare_qty * self.base_fare_unit
        dist = self.distance_qty * self.distance_unit
        wait = self.waiting_qty * self.waiting_unit
        oxy = self.oxygen_qty * self.oxygen_unit
        emer = self.emergency_qty * self.emergency_unit
        night = self.night_qty * self.night_unit

        self.subtotal = base + dist + wait + oxy + emer + night
        return self


class Payment(BaseModel):
    payment_status: str
    payment_method: str
    transaction_id: str


class AmbulanceInvoiceCreate(BaseModel):
    # Patient
    patient_name: str
    patient_age: int
    patient_gender: str
    patient_contact: str

    # Booking
    booking_person: str
    pickup_address: str
    drop_address: str

    # Trip
    ambulance_type: str
    vehicle_number: str
    driver_name: str
    start_time: datetime
    end_time: datetime
    distance: float

    # Charges
    charges: Charges

    # Tax & discount
    tax_percent: float = 0
    discount_amount: float = 0

    # Payment
    payment: Payment

    @property
    def tax_amount(self):
        return (self.charges.subtotal * self.tax_percent) / 100

    @property
    def grand_total(self):
        return self.charges.subtotal + self.tax_amount - self.discount_amount