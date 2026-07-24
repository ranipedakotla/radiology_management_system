from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.security import async_get_db
from app.models.auth import User
from app.core.security import require_roles
from app.schemas.rolebased_schemas import (
    ShiftStart,
    ShiftOut,
    SaleCreate,
    SaleOut,
    DispenseRequest,
    DispenseResponse,
    PurchaseRequestCreate,
    PurchaseRequestOut,
    StockStatusOut,
    PrescriptionUploadOut,
    PharmacistProfileOut,
)
from app.services.shifts_crud import get_pharmacist_profile
from app.services.sales_crud import (
    start_pharmacist_shift,
    end_pharmacist_shift,
    create_pharmacy_sale,
    upload_prescription,
)
from app.services.stock_crud import (
    dispense_medicine,
    get_stock_status,
    create_purchase_request,
    get_low_stock_medicines,
)


router = APIRouter()

@router.get("/profile", response_model=PharmacistProfileOut)
async def pharmacist_profile(
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["pharmacist", "admin","superadmin"]))
):
    pharmacist = await get_pharmacist_profile(db, user.id)

    return PharmacistProfileOut(
        id=pharmacist.id,
        username=pharmacist.username,
        email=pharmacist.email,
        role=pharmacist.role,
    )

@router.post("/shift/start", response_model=ShiftOut)
async def start_shift(
    payload: ShiftStart,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await start_pharmacist_shift(
        db,
        user,
        payload.shift_name
    )

@router.post("/shift/end/{shift_id}", response_model=ShiftOut)
async def end_shift(
    shift_id: int,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await end_pharmacist_shift(db, user, shift_id)

@router.post("/sales/create", response_model=SaleOut)
async def create_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await create_pharmacy_sale(db, user, payload)

@router.post("/dispense", response_model=DispenseResponse)
async def dispense_route(
    payload: DispenseRequest,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await dispense_medicine(db, user, payload)

@router.get("/stock/status", response_model=List[StockStatusOut])
async def get_stock_status_route(
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await get_stock_status(db, user)

@router.get("/stock/low", response_model=List[StockStatusOut])
async def get_low_stock_route(
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await get_low_stock_medicines(db, user)

@router.post("/purchase-request", response_model=PurchaseRequestOut)
async def raise_purchase_request(
    payload: PurchaseRequestCreate,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await create_purchase_request(db, user, payload)

@router.post("/prescriptions/upload", response_model=PrescriptionUploadOut)
async def upload_prescription_route(
    patient_id: Optional[int] = None,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await upload_prescription(
        db,
        user,
        patient_id,
        file
    )