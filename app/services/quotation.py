from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.quotations import Quotation

async def get_quotations(db: AsyncSession):
    result = await db.execute(select(Quotation))
    return result.scalars().all()

async def get_quotation(db: AsyncSession, quotation_id: int):
    result = await db.execute(select(Quotation).filter(Quotation.id == quotation_id))
    return result.scalar_one_or_none()

async def get_quotations_by_medicine(db: AsyncSession, medicine_id: int):
    result = await db.execute(select(Quotation).filter(Quotation.medicine_id == medicine_id))
    return result.scalars().all()

async def create_quotation(db: AsyncSession, quotation):
    db.add(quotation)
    await db.commit()
    await db.refresh(quotation)
    return quotation

async def update_quotation(db: AsyncSession, quotation_id: int, quotation_data: dict):
    quotation = await get_quotation(db, quotation_id)
    if quotation:
        for key, value in quotation_data.items():
            setattr(quotation, key, value)
        await db.commit()
        await db.refresh(quotation)
    return quotation

async def delete_quotation(db: AsyncSession, quotation_id: int):
    quotation = await get_quotation(db, quotation_id)
    if quotation:
        await db.delete(quotation)
        await db.commit()
    return quotation
