from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ambulance import Ambulance
from app.models.ambulance_driver import Driver
from app.models.ambulance_emergency import EmergencyRequest


def assign_driver(db, ambulance_id, driver_id):
    ambulance = db.query(Ambulance).filter(
        Ambulance.id == ambulance_id
    ).first()

    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")

    driver = db.query(Driver).filter(
        Driver.id == driver_id
    ).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver.ambulance_id = ambulance.id

    db.commit()
    db.refresh(driver)

    return {
        "message": "Driver assigned successfully",
        "ambulance_id": ambulance.id,
        "driver_id": driver.id
    }


def create_driver(db, data):

    existing = db.query(Driver).filter(
        Driver.driver_id == data.driver_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Driver ID already exists"
        )

    driver = Driver(**data.dict())

    db.add(driver)
    db.commit()
    db.refresh(driver)

    return driver


def get_drivers(db):
    return db.query(Driver).all()


def update_driver(db, driver_id, data):
    driver = db.query(Driver).get(driver_id)
    for key, value in data.dict(exclude_unset=True).items():
        setattr(driver, key, value)
    db.commit()
    return driver

def delete_driver(db: Session, driver_id: int):

    driver = db.query(Driver).filter(
        Driver.id == driver_id
    ).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    db.delete(driver)
    db.commit()

    return {"message": "Driver deleted successfully"}