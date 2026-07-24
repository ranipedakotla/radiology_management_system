# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func
# from starlette import status
#
# from app.database import get_db
# from app.models.user_models import ShiftLog, User
# from app.schemas.role_based import (
#     ShiftLogCreate,
#     ShiftLogUpdate,
#     ShiftLogResponse
# )
# from app.utils.rolebased_security import get_current_user
# from app.utils.qr_code import generate_qr
#
# router = APIRouter(prefix="/shifts", tags=["Shifts"])
#
# @router.post("/start", response_model=ShiftLogResponse)
# async def start_shift(
#     data: ShiftLogCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     #  Role check (NO ENUM)
#     if current_user.role != "pharmacist":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     shift = ShiftLog(
#         user_id=current_user.id,
#         shift_type=data.shift_type,
#         login_time=data.login_time
#     )
#
#     db.add(shift)
#     await db.commit()
#     await db.refresh(shift)
#     return shift
#
# @router.put("/end/{shift_id}", response_model=ShiftLogResponse)
# async def end_shift(
#     shift_id: int,
#     data: ShiftLogUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "pharmacist":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.id == shift_id)
#     )
#     shift = result.scalar_one_or_none()
#
#     if not shift:
#         raise HTTPException(status_code=404, detail="Shift not found")
#
#     shift.logout_time = data.logout_time
#     shift.total_sales = data.total_sales
#
#     await db.commit()
#     await db.refresh(shift)
#     return shift
#
# @router.get("/{shift_id}", response_model=ShiftLogResponse)
# async def get_shift_by_id(
#     shift_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.id == shift_id)
#     )
#     shift = result.scalar_one_or_none()
#
#     if not shift:
#         raise HTTPException(status_code=404, detail="Shift not found")
#
#     # Pharmacist can see only own shifts
#     if current_user.role == "pharmacist" and shift.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     return shift
# @router.get("/me/list", response_model=list[ShiftLogResponse])
# async def get_my_shifts(
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "pharmacist":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.user_id == current_user.id)
#     )
#     return result.scalars().all()
# @router.get("/", response_model=list[ShiftLogResponse])
# async def get_all_shifts(
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role not in ["admin", "hr"]:
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(select(ShiftLog))
#     return result.scalars().all()
# @router.get("/{shift_id}", response_model=ShiftLogResponse)
# async def get_shift_by_id(
#     shift_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.id == shift_id)
#     )
#     shift = result.scalar_one_or_none()
#
#     if not shift:
#         raise HTTPException(status_code=404, detail="Shift not found")
#
#     # Pharmacist can see only own shifts
#     if current_user.role == "pharmacist" and shift.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     return shift
# @router.put("/{shift_id}", response_model=ShiftLogResponse)
# async def update_shift(
#     shift_id: int,
#     data: ShiftLogUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role not in ["admin", "hr"]:
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.id == shift_id)
#     )
#     shift = result.scalar_one_or_none()
#
#     if not shift:
#         raise HTTPException(status_code=404, detail="Shift not found")
#
#     for field, value in data.dict(exclude_unset=True).items():
#         setattr(shift, field, value)
#
#     await db.commit()
#     await db.refresh(shift)
#     return shift
# @router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_shift(
#     shift_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(ShiftLog).where(ShiftLog.id == shift_id)
#     )
#     shift = result.scalar_one_or_none()
#
#     if not shift:
#         raise HTTPException(status_code=404, detail="Shift not found")
#
#     await db.delete(shift)
#     await db.commit()
# @router.get("/summary/{user_id}")
# async def shift_summary(
#     user_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role not in ["admin", "hr"]:
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(
#             func.count(ShiftLog.id).label("total_shifts"),
#             func.sum(ShiftLog.total_sales).label("total_sales")
#         ).where(ShiftLog.user_id == user_id)
#     )
#
#     summary = result.one()
#
#     return {
#         "user_id": user_id,
#         "total_shifts": summary.total_shifts or 0,
#         "total_sales": summary.total_sales or 0
#     }
#
# @router.get("/qr")
# async def medicine_docs_qr():
#     url = "http://localhost:8000/docs#/Medicines"
#     return generate_qr(url)