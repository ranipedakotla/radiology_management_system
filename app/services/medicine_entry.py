from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, asc
from app.models.entry_models import Medicine, Batch
from app.schemas.entry_schemas import MedicineCreate, MedicineUpdate

# async def create_medicine(
#     db: AsyncSession,
#     medicine: MedicineCreate
# ) -> Medicine:

#     db_obj = Medicine(**medicine.dict())

#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)

#     return db_obj

# async def create_medicine(db: AsyncSession, medicine: MedicineCreate):

#     # medicine_data = medicine.model_dump()   # convert to dict

#     db_obj = Medicine(**medicine_data)

#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)

#     return db_obj

async def create_medicine(db: AsyncSession, medicine_data: dict):

    db_obj = Medicine(**medicine_data)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    return db_obj


async def get_medicine(
    db: AsyncSession,
    medicine_id: int,
    hospital_id: int,
    branch_id: int
):
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.hospital_id == hospital_id,
            Medicine.branch_id == branch_id
        )
    )
    return result.scalar_one_or_none()

async def get_medicines(db: AsyncSession, skip: int, limit: int, search: str | None = None):
    query = select(Medicine).offset(skip).limit(limit)
    if search:
        query = query.where(
            or_(
                Medicine.item_name.ilike(f"%{search}%"),
                Medicine.brand_name.ilike(f"%{search}%"),
                Medicine.company.ilike(f"%{search}%")
            )
        )
    result = await db.execute(query)
    return result.scalars().all()

async def update_medicine(
    db: AsyncSession,
    medicine_id: int,
    medicine_update: MedicineUpdate,
    hospital_id: int,
    branch_id: int
):

    medicine = await get_medicine(
        db, medicine_id, hospital_id, branch_id
    )

    if not medicine:
        return None

    for field, value in medicine_update.dict(
        exclude_unset=True
    ).items():
        setattr(medicine, field, value)

    await db.commit()
    await db.refresh(medicine)

    return medicine
async def delete_medicine(
    db: AsyncSession,
    medicine_id: int,
    hospital_id: int,
    branch_id: int
):

    medicine = await get_medicine(
        db, medicine_id, hospital_id, branch_id
    )

    if not medicine:
        return False

    await db.delete(medicine)
    await db.commit()

    return True
#
# async def get_fefo_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     medicine_id: int,
#     required_qty: int,
# ) -> Batch | None:
#
#     result = await db.execute(
#         select(Batch)
#         .where(
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#             Batch.medicine_id == medicine_id,
#             Batch.quantity_available >= required_qty,
#             Batch.expiry_date >= date.today(),
#         )
#         .order_by(asc(Batch.expiry_date))
#         .limit(1)
#     )
#
#     return result.scalar_one_or_none()

async def get_fefo_batch(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    medicine_id: int,
    required_qty: int,
):
    result = await db.execute(
        select(Batch)
        .where(
            Batch.hospital_id == hospital_id,
            Batch.branch_id == branch_id,
            Batch.medicine_id == medicine_id,
            Batch.quantity_available >= required_qty,
            Batch.expiry_date >= date.today(),
        )
        .order_by(Batch.expiry_date.asc())
        .limit(1)
    )

    return result.scalar_one_or_none()