from app.models.auth import User
from app.models.blood_bank import UserRole
from app.schemas.ambulance_driver import DriverResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_db, require_roles
from app.schemas.ambulance_driver import DriverCreate, DriverUpdate
from app.services import ambulance_driver

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.post("/assign")
def assign_driver(ambulance_id: int, driver_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_driver.assign_driver(db, ambulance_id, driver_id)

@router.post("/create-driver", response_model=DriverResponse)
def create(data: DriverCreate, db: Session = Depends(get_db),
           user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN,UserRole.RECEPTIONIST]))):

    return ambulance_driver.create_driver(db, data)


@router.get("/list-drivers", response_model=list[DriverResponse])
def list_all(db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_driver.get_drivers(db)


@router.patch("/{id}", response_model=DriverResponse)
def update(id: int, data: DriverUpdate, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_driver.update_driver(db, id, data)

@router.delete("/{driver_id}")
def delete_driver(driver_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_driver.delete_driver(db, driver_id)