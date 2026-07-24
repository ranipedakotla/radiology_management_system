# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.models.entry_models import Medicine
#
# async def get_medicines(db: AsyncSession):
#     result = await db.execute(select(Medicine))
#     return result.scalars().all()
#
# async def get_medicine(db: AsyncSession, medicine_id: int):
#     result = await db.execute(select(Medicine).filter(Medicine.id == medicine_id))
#     return result.scalar_one_or_none()
#
# async def get_low_stock_medicines(db: AsyncSession):
#     result = await db.execute(
#         select(Medicine).filter(Medicine.stock <= Medicine.reorder_level)
#     )
#     return result.scalars().all()
#
# async def create_medicine(db: AsyncSession, medicine):
#     db.add(medicine)
#     await db.commit()
#     await db.refresh(medicine)
#     return medicine
#
# async def update_medicine(db: AsyncSession, medicine_id: int, medicine_data: dict):
#     medicine = await get_medicine(db, medicine_id)
#     if medicine:
#         for key, value in medicine_data.items():
#             setattr(medicine, key, value)
#         await db.commit()
#         await db.refresh(medicine)
#     return medicine
#
# async def delete_medicine(db: AsyncSession, medicine_id: int):
#     medicine = await get_medicine(db, medicine_id)
#     if medicine:
#         await db.delete(medicine)
#         await db.commit()
#     return medicine
