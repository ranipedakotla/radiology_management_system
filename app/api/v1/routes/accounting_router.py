from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils.qr_code import generate_qr
from app.core.security import async_get_db
from app.models.accounting import Ledger
from app.schemas.accounting import LedgerCreate, LedgerUpdate, LedgerOut

router = APIRouter(prefix="/ledger",tags=["Ledger / Accounting"])


@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)



@router.post("/", response_model=LedgerOut)
async def create_ledger(
    hospital_id: int,
    branch_id: int,
    data: LedgerCreate,
    db: AsyncSession = Depends(async_get_db)
):
    ledger = Ledger(
        ledger_type=data.ledger_type,
        amount=data.amount,
        hospital_id=hospital_id,
        branch_id=branch_id
    )

    db.add(ledger)
    await db.commit()
    await db.refresh(ledger)

    return ledger

@router.get("/", response_model=list[LedgerOut])
async def get_all_ledgers(
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db)
):
    result = await db.execute(
        select(Ledger).where(
            Ledger.hospital_id == hospital_id,
            Ledger.branch_id == branch_id
        )
    )

    return result.scalars().all()

@router.get("/{ledger_id}", response_model=LedgerOut)
async def get_ledger(
    ledger_id: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db)
):
    result = await db.execute(
        select(Ledger).where(
            Ledger.id == ledger_id,
            Ledger.hospital_id == hospital_id,
            Ledger.branch_id == branch_id
        )
    )

    ledger = result.scalar_one_or_none()

    if not ledger:
        raise HTTPException(404, "Ledger entry not found")

    return ledger

@router.put("/{ledger_id}", response_model=LedgerOut)
async def update_ledger(
    hospital_id: int,
    branch_id: int,
    ledger_id: int,
    data: LedgerUpdate,
    db: AsyncSession = Depends(async_get_db)
):
    result = await db.execute(
        select(Ledger).where(
            Ledger.id == ledger_id,
            Ledger.hospital_id == hospital_id,
            Ledger.branch_id == branch_id
        )
    )

    ledger = result.scalar_one_or_none()

    if not ledger:
        raise HTTPException(404, "Ledger entry not found")

    update_data = data.model_dump(exclude_unset=True)

    # Prevent invalid hospital_id
    if "hospital_id" in update_data and update_data["hospital_id"] <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid hospital_id"
        )

    # Prevent invalid branch_id
    if "branch_id" in update_data and update_data["branch_id"] <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid branch_id"
        )
        # Validate ledger_type
    if "ledger_type" in update_data:
        if not update_data["ledger_type"] or not update_data["ledger_type"].strip():
            raise HTTPException(
                status_code=400,
                detail="Ledger type cannot be empty"
            )

        # Validate amount
    if "amount" in update_data:
        if update_data["amount"] is None:
            raise HTTPException(
                status_code=400,
                detail="Amount cannot be null"
            )
        if update_data["amount"] < 0:
            raise HTTPException(
                status_code=400,
                detail="Amount cannot be negative"
            )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ledger, key, value)

    # await db.commit()
    # await db.refresh(ledger)
    #
    # return ledger
    try:
        await db.commit()
        await db.refresh(ledger)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid foreign key value (hospital_id or branch_id)."
        )

    return ledger

@router.delete("/{ledger_id}", status_code=200)
async def delete_ledger(
    hospital_id: int,
    branch_id: int,
    ledger_id: int,
    db: AsyncSession = Depends(async_get_db)
):
    result = await db.execute(
        select(Ledger).where(
            Ledger.id == ledger_id,
            Ledger.hospital_id == hospital_id,
            Ledger.branch_id == branch_id
        )
    )

    ledger = result.scalar_one_or_none()

    if not ledger:
        raise HTTPException(404, "Ledger entry not found")

    await db.delete(ledger)
    await db.commit()
    return {"message": "Ledger deleted successfully"}


