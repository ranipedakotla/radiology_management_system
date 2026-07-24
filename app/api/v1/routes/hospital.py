from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.auth import User
from app.models.org import Hospital as HospitalModel, Hospital
from app.schemas.hospital_schemas import (
    Hospital as HospitalSchema,
    HospitalBase,
)
from app.core.security import async_get_db, require_roles

router = APIRouter(prefix="/hospital", tags=["Hospital"])



# @router.post("/", response_model=HospitalSchema)
# async def create_main_hospital(
#     hospital: HospitalBase,
#     db: AsyncSession = Depends(get_db),
# ):
#
#     db_hospital = HospitalModel(**hospital.model_dump())
#
#     db.add(db_hospital)
#     await db.commit()
#
#
#     result = await db.execute(
#         select(HospitalModel)
#         .options(selectinload(HospitalModel.branches))
#         .where(HospitalModel.id == db_hospital.id)
#     )
#
#     return result.scalars().first()

@router.post("/", response_model=HospitalSchema)
async def create_main_hospital(
    hospital: HospitalBase,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("superadmin")),
):

    # Check existing hospital
    result = await db.execute(
        select(Hospital).limit(1)
    )
    existing_hospital = (
        await db.execute(select(Hospital))
    ).scalars().first()

    if existing_hospital:
        raise HTTPException(
            status_code=400,
            detail="Main hospital already exists"
        )

    db_hospital = Hospital(**hospital.model_dump())

    db.add(db_hospital)

    await db.commit()
    await db.refresh(db_hospital)

    result = await db.execute(
        select(Hospital)
        .options(selectinload(Hospital.branches))
        .where(Hospital.id == db_hospital.id)
    )

    return result.scalars().first()



@router.get("/main", response_model=HospitalSchema)
async def get_main_hospital(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("superadmin")),
):

    result = await db.execute(
        select(HospitalModel).options(
            selectinload(HospitalModel.branches)
        )
    )

    hospital = result.scalars().first()

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Main hospital not configured"
        )
    return hospital


@router.put("/", response_model=HospitalSchema)
async def update_main_hospital(
    hospital: HospitalBase,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("superadmin")),
):

    result = await db.execute(select(HospitalModel))
    db_hospital = result.scalars().first()

    if not db_hospital:
        raise HTTPException(404, "Main hospital not configured")

    for key, value in hospital.model_dump(exclude_unset=True).items():
        setattr(db_hospital, key, value)

    await db.commit()
    await db.refresh(db_hospital)


    result = await db.execute(
        select(HospitalModel)
        .options(selectinload(HospitalModel.branches))
        .where(HospitalModel.id == db_hospital.id)
    )

    return result.scalars().first()


@router.delete("/", status_code=204)
async def delete_main_hospital(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("superadmin")),
):

    result = await db.execute(select(HospitalModel))
    hospital = result.scalars().first()

    if not hospital:
        raise HTTPException(404, "Main hospital not found")

    await db.delete(hospital)
    await db.commit()

    return Response(status_code=204)