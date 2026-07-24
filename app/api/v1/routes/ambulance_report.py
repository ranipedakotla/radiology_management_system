from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_db, require_roles
from app.models.ambulance_emergency import EmergencyRequest
from app.models.auth import User
from app.models.blood_bank import UserRole
from app.schemas.ambulance_patient_transport import TripResponse
from app.services import ambulance_report

router = APIRouter(prefix="/reports", tags=["Ambulance_Reports"])

#  Create Trip
@router.post("/start/{request_id}", response_model=TripResponse)
def create_trip(request_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_report.create_trip(db, request_id)


@router.get("/total-trips")
def total_trips(
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles([
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.RECEPTIONIST
        ])
    )
):
    return {"total_trips": db.query(EmergencyRequest).count()}


@router.get("/completed-trips")
def completed_trips(db: Session = Depends(get_db),
                user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_report.completed_trips(db)

#  Get Trip Details
@router.get("/{request_id}", response_model=TripResponse)
def get_trip(request_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_report.get_trip_by_request_id(db, request_id)

#  End Trip
@router.put("/end/{request_id}", response_model=TripResponse)
def end_trip(request_id: int, distance_km: float, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_report.end_trip(db, request_id, distance_km)

