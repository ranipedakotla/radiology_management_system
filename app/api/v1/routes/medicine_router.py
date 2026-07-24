# # from fastapi import APIRouter, Depends, HTTPException, Query
# # from sqlalchemy.ext.asyncio import AsyncSession
# # from sqlalchemy.future import select
# # from sqlalchemy import or_
# # from starlette import status
# #
# # from app.database import get_db
# # from app.models.medicine import Medicine
# # from app.schemas.vendor import MedicineCreate, MedicineOut
# #
# #
# # router = APIRouter(prefix="/medicines", tags=["Medicines"])
# #
# # @router.get("/")
# # async def get_all_medicines(db: AsyncSession = Depends(get_db)):
# #     result = await db.execute(select(Medicine))
# #     return result.scalars().all()
# #
# # router = APIRouter(prefix="/medicines", tags=["Medicines"])
# #
# # @router.post("/", response_model=MedicineOut)
# # async def create_medicine(data: MedicineCreate, db: AsyncSession = Depends(get_db)):
# #     med = Medicine(**data.dict())
# #     db.add(med)
# #     await db.commit()
# #     await db.refresh(med)
# #     return med
# #
# # @router.get("/", response_model=list[MedicineOut])
# # async def get_all_medicines(
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     result = await db.execute(select(Medicine))
# #     medicines = result.scalars().all()
# #     return medicines
# # @router.get("/search", response_model=list[MedicineOut])
# # async def search_medicines(
# #     name: str | None = Query(None),
# #     dosage: str | None = Query(None),
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     query = select(Medicine)
# #
# #     if name and dosage:
# #
# #         query = query.where(
# #             or_(
# #                 Medicine.name.ilike(f"%{name}%"),
# #                 Medicine.dosage.ilike(f"%{dosage}%")
# #             )
# #         )
# #     elif name:
# #         query = query.where(Medicine.name.ilike(f"%{name}%"))
# #     elif dosage:
# #         query = query.where(Medicine.dosage.ilike(f"%{dosage}%"))
# #
# #     result = await db.execute(query)
# #     return result.scalars().all()
# # @router.get("/{medicine_id}", response_model=MedicineOut)
# # async def get_medicine_by_id(
# #     medicine_id: int,
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     result = await db.execute(
# #         select(Medicine).where(Medicine.id == medicine_id)
# #     )
# #     medicine = result.scalar_one_or_none()
# #
# #     if not medicine:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND,
# #             detail="Medicine not found"
# #         )
# #
# #     return medicine
# #
# # @router.put("/{medicine_id}", response_model=MedicineOut)
# # async def update_medicine(
# #     medicine_id: int,
# #     data: MedicineCreate,
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     result = await db.execute(
# #         select(Medicine).where(Medicine.id == medicine_id)
# #     )
# #     medicine = result.scalar_one_or_none()
# #
# #     if not medicine:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND,
# #             detail="Medicine not found"
# #         )
# #
# #     for field, value in data.dict().items():
# #         setattr(medicine, field, value)
# #
# #     await db.commit()
# #     await db.refresh(medicine)
# #     return medicine
# #
# # @router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
# # async def delete_medicine(
# #     medicine_id: int,
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     result = await db.execute(
# #         select(Medicine).where(Medicine.id == medicine_id)
# #     )
# #     medicine = result.scalar_one_or_none()
# #
# #     if not medicine:
# #         raise HTTPException(
# #             status_code=status.HTTP_404_NOT_FOUND,
# #             detail="Medicine not found"
# #         )
# #
# #     await db.delete(medicine)
# #     await db.commit()
# from app.core.security import async_get_db
# from app.models.entry_models import Medicine
# from app.schemas.vendor import MedicineCreate, MedicineOut
# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy import or_, asc, desc, func
# from starlette import status
# from app.utils.qr_code import generate_qr
#
#
# router = APIRouter(prefix="/medicines", tags=["Medicines"])
#
#
# @router.post("/", response_model=MedicineOut)
# async def create_medicine(
#     data: MedicineCreate,
#     db: AsyncSession = Depends(async_get_db)
# ):
#     med = Medicine(**data.model_dump())
#     db.add(med)
#     await db.commit()
#     await db.refresh(med)
#     return med
#
#
#
# @router.get("/", response_model=list[MedicineOut])
# async def get_all_medicines(
#     order: str = Query("asc", enum=["asc", "desc"]),
#     db: AsyncSession = Depends(async_get_db)
# ):
#     order_by = asc(Medicine.name) if order == "asc" else desc(Medicine.name)
#
#     result = await db.execute(
#         select(Medicine).order_by(order_by)
#     )
#     return result.scalars().all()
#
#
# # ---------------- SEARCH (Alphabetical) ----------------
# # @router.get("/search", response_model=list[MedicineOut])
# # async def search_medicines(
# #     name: str | None = Query(None),
# #     dosage: str | None = Query(None),
# #     order: str = Query("asc", enum=["asc", "desc"]),
# #     db: AsyncSession = Depends(get_db)
# # ):
# #     query = select(Medicine)
# #
# #     if name and dosage:
# #         query = query.where(
# #             or_(
# #                 Medicine.name.ilike(f"%{name}%"),
# #                 Medicine.strength.ilike(f"%{dosage}%"),
# #                 Medicine.dosage_form.ilike(f"%{dosage}%")
# #             )
# #         )
# #     elif name:
# #         query = query.where(Medicine.name.ilike(f"%{name}%"))
# #     elif dosage:
# #         query = query.where(Medicine.dosage.ilike(f"%{dosage}%"))
# #
# #     order_by = asc(Medicine.name) if order == "asc" else desc(Medicine.name)
# #     query = query.order_by(order_by)
# #
# #     result = await db.execute(query)
# #     return result.scalars().all()
#
# @router.get("/qr")
# async def medicine_docs_qr():
#     url = "http://localhost:8000/docs#/Medicines"
#     return generate_qr(url)
#
# @router.get("/search", response_model=list[MedicineCreate])
# async def search_medicines(
#         q: str | None = Query(None, description="A-Z OR item_name/strength/brand_name/company search"),
#         db: AsyncSession = Depends(async_get_db)
# ):
#     query = select(Medicine)
#
#     if q:
#         search_term = q.strip().lower()
#
#         if len(search_term) == 1 and search_term.isalpha():
#             query = query.where(
#                 or_(
#                     func.lower(Medicine.name).like(f"{search_term}%"),
#                     func.lower(Medicine.dosage_form).like(f"{search_term}%"),
#                     # func.lower(Medicine.brand_name).like(f"{search_term}%"),
#                     func.lower(Medicine.company).like(f"{search_term}%")
#                 )
#             )
#
#         else:
#             query = query.where(
#                 or_(
#                     func.lower(Medicine.name).like(f"{search_term}%"),
#                     func.lower(Medicine.dosage_form).like(f"{search_term}%"),
#                     # func.lower(Medicine.brand_name).like(f"{search_term}%"),
#                     func.lower(Medicine.company).like(f"{search_term}%")
#                 )
#             )
#
#     query = query.order_by(Medicine.name.asc())
#     result = await db.execute(query)
#     return result.scalars().all()
#
#
# @router.get("/search", response_model=list[MedicineCreate])
# async def search_medicines(
#         q: str | None = Query(None, description="A-Z OR item_name/strength/company search"),
#         db: AsyncSession = Depends(async_get_db)
# ):
#     query = select(Medicine)
#
#     if q:
#         search_term = q.strip().lower()
#
#         if len(search_term) == 1 and search_term.isalpha():
#             query = query.where(
#                 or_(
#                     func.lower(Medicine.name).like(f"{search_term}%"),
#                     func.lower(Medicine.dosage_form).like(f"{search_term}%"),
#                     # func.lower(Medicine.brand_name).like(f"{search_term}%"),
#                     func.lower(Medicine.company).like(f"{search_term}%")
#                 )
#             )
#
#         else:
#             query = query.where(
#                 or_(
#                     func.lower(Medicine.name).like(f"{search_term}%"),
#                     func.lower(Medicine.dosage_form).like(f"{search_term}%"),
#                     # func.lower(Medicine.brand_name).like(f"{search_term}%"),
#                     func.lower(Medicine.company).like(f"{search_term}%")
#                 )
#             )
#
#     query = query.order_by(Medicine.item_name.asc())
#     result = await db.execute(query)
#     return result.scalars().all()
#
#
# # ---------------- GET BY ID ----------------
# @router.get("/{medicine_id:int}", response_model=MedicineOut)
# async def get_medicine_by_id(
#     medicine_id: int,
#     db: AsyncSession = Depends(async_get_db)
# ):
#     result = await db.execute(
#         select(Medicine).where(Medicine.id == medicine_id)
#     )
#     medicine = result.scalar_one_or_none()
#
#     if not medicine:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Medicine not found"
#         )
#
#     return medicine
#
#
# # ---------------- UPDATE ----------------
# @router.put("/{medicine_id}", response_model=MedicineOut)
# async def update_medicine(
#     medicine_id: int,
#     data: MedicineCreate,
#     db: AsyncSession = Depends(async_get_db)
# ):
#     result = await db.execute(
#         select(Medicine).where(Medicine.id == medicine_id)
#     )
#     medicine = result.scalar_one_or_none()
#
#     if not medicine:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Medicine not found"
#         )
#
#     for field, value in data.model_dump().items():
#         setattr(medicine, field, value)
#
#     await db.commit()
#     await db.refresh(medicine)
#     return medicine
#
#
# # ---------------- DELETE ----------------
# @router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_medicine(
#     medicine_id: int,
#     db: AsyncSession = Depends(async_get_db)
# ):
#     result = await db.execute(
#         select(Medicine).where(Medicine.id == medicine_id)
#     )
#     medicine = result.scalar_one_or_none()
#
#     if not medicine:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Medicine not found"
#         )
#
#     await db.delete(medicine)
#     await db.commit()
# #
# # @router.get("/qr")
# # async def medicine_docs_qr():
# #     url = "http://localhost:8000/docs#/Medicines"
# #     return generate_qr(url)