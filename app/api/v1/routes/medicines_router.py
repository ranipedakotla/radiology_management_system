# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.security import get_db
# from app.models.entry_models import Medicine
# from app.schemas.requirment_schemas import MedicineCreate, MedicineOut
# from app.services.medicine_entry import (
#     get_medicines, get_medicine, get_low_stock_medicines,
#     create_medicine, update_medicine, delete_medicine
# )
#
# router = APIRouter(prefix="/medicines", tags=["Medicines"])
#
# @router.get("/", response_model=list[MedicineOut])
# async def list_medicines(db: AsyncSession = Depends(get_db)):
#     return await get_medicines(db)
#
# @router.get("/low-stock", response_model=list[MedicineOut])
# async def list_low_stock_medicines(db: AsyncSession = Depends(get_db)):
#     return await get_low_stock_medicines(db)
#
# @router.get("/{medicine_id}", response_model=MedicineOut)
# async def get_medicine(medicine_id: int, db: AsyncSession = Depends(get_db)):
#     medicine = await get_medicine(db, medicine_id)
#     if not medicine:
#         raise HTTPException(status_code=404, detail="Medicine not found")
#     return medicine
#
# @router.post("/", response_model=MedicineOut)
# async def create_medicine(med: MedicineCreate, db: AsyncSession = Depends(get_db)):
#     med_obj = Medicine(**med.dict())
#     return await create_medicine(db, med_obj)
#
# @router.put("/{medicine_id}", response_model=MedicineOut)
# async def update_medicine(medicine_id: int, med_data: MedicineCreate, db: AsyncSession = Depends(get_db)):
#     medicine = await update_medicine(db, medicine_id, med_data.dict(exclude_unset=True))
#     if not medicine:
#         raise HTTPException(status_code=404, detail="Medicine not found")
#     return medicine
#
# @router.delete("/{medicine_id}")
# async def delete_medicine(medicine_id: int, db: AsyncSession = Depends(get_db)):
#     medicine = await delete_medicine(db, medicine_id)
#     if not medicine:
#         raise HTTPException(status_code=404, detail="Medicine not found")
#     return {"message": "Medicine deleted successfully"}
