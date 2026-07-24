from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ambulance_driver import Driver
from app.models.ambulance_emergency import EmergencyRequest
from app.models.ambulance import Ambulance, AmbulanceStatus
import math

from app.schemas.ambulance import AmbulanceType


def assign_ambulance(db, request_id, ambulance_id):

    request = db.query(EmergencyRequest).filter(
        EmergencyRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    ambulance = db.query(Ambulance).filter(
        Ambulance.id == ambulance_id
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")

    if ambulance.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Ambulance is busy")

    driver = db.query(Driver).filter(
        Driver.ambulance_id == ambulance.id
    ).first()

    if not driver:
        raise HTTPException(
            status_code=400,
            detail="No driver assigned to this ambulance"
        )

    if driver.active_status != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Driver is not active"
        )

    request.ambulance_id = ambulance.id
    request.status = "ASSIGNED"

    ambulance.status = "BUSY"
    driver.active_status = "BUSY"

    db.commit()

    db.refresh(request)
    db.refresh(driver)

    return {
        "message": "Ambulance and Driver assigned successfully",
        "request_id": request.id,
        "ambulance_id": ambulance.id,
        "driver_id": driver.id,
        "driver_name": driver.driver_name
    }


def create_ambulance(db, data):

    existing = db.query(Ambulance).filter(
        Ambulance.registration_number == data.registration_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Registration number already exists"
        )

    amb = Ambulance(**data.dict())

    db.add(amb)
    db.commit()
    db.refresh(amb)

    return amb


def get_ambulances(db):
    return db.query(Ambulance).all()


def update_status(db, ambulance_id, status):
    amb = db.query(Ambulance).get(ambulance_id)
    amb.status = status
    db.commit()
    return amb

def create_booking(db, data):

    ambulance = db.query(Ambulance).filter(
        Ambulance.id == data.ambulance_id
    ).first()

    if not ambulance:
        raise HTTPException(
            status_code=404,
            detail="Ambulance not found"
        )

    request = EmergencyRequest(**data.dict())

    db.add(request)
    db.commit()
    db.refresh(request)

    return request


def get_booking(db, request_id):
    return db.query(EmergencyRequest).get(request_id)


def list_bookings(db):
    return db.query(EmergencyRequest).all()



# def delete_ambulance(db: Session, ambulance_id: int):
#
#     ambulance = db.query(Ambulance).filter(
#         Ambulance.id == ambulance_id
#     ).first()
#
#     if not ambulance:
#         raise HTTPException(status_code=404, detail="Ambulance not found")
#
#     # 🔥 Important: Remove driver relation safely
#     if ambulance.driver:
#         ambulance.driver.ambulance_id = None   # unlink driver
#
#     db.delete(ambulance)
#     db.commit()
#
#     return {"message": "Ambulance deleted successfully"}