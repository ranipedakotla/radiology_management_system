from app.models.ambulance import Ambulance
from app.models.ambulance_emergency import EmergencyRequest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.ambulance_patient_transports import Trip

# 🔹 Create Trip (when ambulance assigned or trip starts)
def create_trip(db: Session, request_id: int):
    request = db.query(EmergencyRequest).filter(
        EmergencyRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    trip = Trip(
        request_id=request.id,
        ambulance_id=request.ambulance_id,
        hospital_id=request.hospital_id,
        start_time=datetime.now()
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


# 🔹 Get Trip by request_id
def get_trip_by_request_id(db: Session, request_id: int):
    trip = db.query(Trip).filter(
        Trip.request_id == request_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


def end_trip(db: Session, request_id: int, distance: float):

    trip = db.query(Trip).filter(
        Trip.request_id == request_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    request = db.query(EmergencyRequest).filter(
        EmergencyRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Emergency request not found")

    # Complete trip
    trip.end_time = datetime.now()
    trip.distance_km = distance

    # Update request status
    request.status = "COMPLETED"

    # Make ambulance available again
    if request.ambulance_id:
        ambulance = db.query(Ambulance).filter(
            Ambulance.id == request.ambulance_id
        ).first()

        if ambulance:
            ambulance.status = "AVAILABLE"

            if ambulance.driver:
                ambulance.driver.active_status = "ACTIVE"

    db.commit()

    db.refresh(trip)
    db.refresh(request)

    return {
        "message": "Trip completed successfully",
        "request_id": request.id,
        "trip_id": trip.id,
        "distance_km": trip.distance_km,
        "status": request.status
    }

def total_trips(db):
    count = db.query(EmergencyRequest).count()
    return {"total_trips": count}


def completed_trips(db):
    return db.query(EmergencyRequest).filter(
        EmergencyRequest.status == "COMPLETED"
    ).count()

