from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_db, require_roles
from app.models.auth import User
from app.models.blood_bank import UserRole
from app.schemas.ambulance import AmbulanceCreate, AmbulanceResponse

from app.schemas.ambulance_emergency import EmergencyRequestCreate
from app.services import ambulance

router = APIRouter(prefix="/ambulance", tags=["Ambulance"])

@router.post("/ambulance_create",response_model=AmbulanceResponse)
def ambulance_create(data: AmbulanceCreate, db: Session = Depends(get_db),
                     user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))
                     ):
    return ambulance.create_ambulance(db, data)


@router.get("/list_all_ambulances", response_model=list[AmbulanceResponse])
def list_all_ambulances(db: Session = Depends(get_db),
                        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))
                        ):
    return ambulance.get_ambulances(db)


@router.patch("/{id}/status",response_model=AmbulanceResponse)
def update(id: int, status: str, db: Session = Depends(get_db),
           user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))):
    return ambulance.update_status(db, id, status)

@router.post("/assign_ambulance")
def assign(request_id: int, ambulance_id: int, db: Session = Depends(get_db)
           ,user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))):
    return ambulance.assign_ambulance(db, request_id, ambulance_id)

@router.post("/emergency")
def emergency_create(
    data: EmergencyRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles([
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
            UserRole.RECEPTIONIST
        ])
    )
):
    return ambulance.create_booking(db, data)


@router.get("/{request_id}")
def get(request_id: int, db: Session = Depends(get_db),
        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):
    return ambulance.get_booking(db, request_id)


@router.get("/list_all_requests")
def list_all(db: Session = Depends(get_db),
             user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))):
    return ambulance.list_bookings(db)
#
# @router.delete("/{ambulance_id}")
# def delete_ambulance(ambulance_id: int, db: Session = Depends(get_db)):
#     return ambulance_services.delete_ambulance(db, ambulance_id)