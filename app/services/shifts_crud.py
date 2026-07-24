from sqlalchemy import select, and_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, time, datetime
from fastapi import HTTPException
from app.models.user_models import Shift, UserShift
from app.models.auth import User
# from app.routers.admin_router import create_shift
from app.schemas.rolebased_schemas import ShiftOperation, ShiftResponse,ShiftOperationResponse,ShiftAssign
from app.core.security import PREDEFINED_SHIFTS


def parse_time(time_str: str) -> time:
    return datetime.strptime(time_str, "%H:%M").time()


async def manage_shift_operations(db: AsyncSession, operation: ShiftOperation, current_user):
    op = operation.operation.lower()

    if op.startswith("create_"):
        return await create_shift_from_template(db, operation, op)
    elif op.startswith("update_"):
        return await _update_shift(db, operation, op)
    elif op.startswith("delete_"):
        return await _delete_shift(db, op)
    elif op.startswith("assign_user_"):
        return await assign_shift_operation(db, operation, op)
    else:
        raise HTTPException(status_code=400, detail="Invalid operation")


# async def _create_shift(db: AsyncSession, operation: ShiftOperation, op: str):
#     shift_key = op.replace("create_", "").upper()
#     if shift_key not in PREDEFINED_SHIFTS:
#         raise HTTPException(status_code=400, detail=f"Unknown shift type: {shift_key}")
#
#     #Get template data (strings)
#     template_data = PREDEFINED_SHIFTS[shift_key].copy()
#     template_data["name"] = shift_key
#
#     #Override with request data if provided
#     if operation.start_time:
#         template_data["start_time"] = operation.start_time
#     if operation.end_time:
#         template_data["end_time"] = operation.end_time
#
#     #Check if shift exists
#     result = await db.execute(select(Shift).where(Shift.name == shift_key))
#     if result.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail=f"Shift '{shift_key}' already exists")
#
#
#     shift_data = {
#         "name": template_data["name"],
#         "start_time": parse_time(template_data["start_time"]),
#         "end_time": parse_time(template_data["end_time"])
#     }
#
#     shift = Shift(**shift_data)
#     db.add(shift)
#     await db.commit()
#     await db.refresh(shift)
#     return ShiftOperationResponse(
#         success=True,
#         message=f"Shift {shift_key} created successfully",
#         shift_id=shift.id
#     )
async def create_shift_from_template(db: AsyncSession, code: str, user: User):
    code = code.upper()

    if code not in PREDEFINED_SHIFTS:
        raise HTTPException(400, "Invalid shift code")

    exists = await db.execute(
        select(Shift).where(
            Shift.name == code,
            Shift.hospital_id == user.hospital_id,
            Shift.branch_id == user.current_branch_id
        )
    )

    if exists.scalar_one_or_none():
        raise HTTPException(400, "Shift already exists")

    tpl = PREDEFINED_SHIFTS[code]

    shift = Shift(
        name=code,
        start_time=parse_time(tpl["start_time"]),
        end_time=parse_time(tpl["end_time"]),
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        # created_by=user.id
    )

    db.add(shift)
    await db.commit()
    await db.refresh(shift)

    return ShiftOperationResponse(
        success=True,
        message=f"Shift {code} created",
        shift_id=shift.id
    )



async def _update_shift(db: AsyncSession, operation: ShiftOperation, op: str):
    shift_id = int(op.split("_")[1])
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    update_data = operation.model_dump(exclude_unset=True, exclude={"operation"})
    for field, value in update_data.items():
        if field in ["start_time", "end_time"] and value:
            setattr(shift, field, parse_time(value))

    await db.commit()
    await db.refresh(shift)
    return ShiftOperationResponse(
        success=True,
        message=f"Shift {shift_id} updated"
    )

async def _delete_shift(db: AsyncSession, op: str):
    shift_id = int(op.split("_")[1])
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    shift.is_active = False
    await db.commit()
    return {"success": True, "message": "Shift soft-deleted"}

# async def _assign_user_shift(db: AsyncSession, operation: ShiftOperation, op: str):
#     parts = op.split("_")
#     user_id = int(parts[2])
#     shift_id = int(parts[4])
#     assigned_date_str = "_".join(parts[5:]).replace("_", "-") if len(parts) > 5 else str(date.today())
#     assigned_date = date.fromisoformat(assigned_date_str)
#
#     user = await _get_pharmacist(db, user_id)
#     shift_obj = await _get_active_shift(db, shift_id)
#
#     existing = await db.execute(
#         select(UserShift).where(
#             and_(
#                 UserShift.user_id == user_id,
#                 UserShift.shift_id == shift_id,
#                 UserShift.assigned_date == assigned_date,
#             )
#         )
#     )
#     if existing.scalar_one_or_none():
#         return {"error": "Shift already assigned for this date"}
#
#     assignment = UserShift(user_id=user_id, shift_id=shift_id, assigned_date=assigned_date)
#     db.add(assignment)
#     await db.commit()
#     return {"success": True, "message": f"Shift assigned to {user.username}"}

async def assign_shift(db: AsyncSession, data: ShiftAssign):
    user = await db.get(User, data.user_id)
    if not user or user.role != "PHARMACIST":
        raise HTTPException(404, "Pharmacist not found")

    shift = await db.get(Shift, data.shift_id)
    if not shift:
        raise HTTPException(404, "Shift not found")

    existing = await db.execute(
        select(UserShift).where(
            UserShift.user_id == data.user_id,
            UserShift.assigned_date == data.assigned_date
        )
    )

    if existing.scalar():
        raise HTTPException(400, "Shift already assigned for that date")

    row = UserShift(
        user_id=data.user_id,
        shift_id=data.shift_id,
        assigned_date=data.assigned_date
    )

    db.add(row)
    await db.commit()

    return ShiftOperationResponse(
        success=True,
        message="Shift assigned",
        shift_id=data.shift_id,
        affected_users=[data.user_id]
    )



async def _get_pharmacist(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id, User.role == "PHARMACIST"))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Pharmacist not found")
    return user

async def _get_active_shift(db: AsyncSession, shift_id: int):
    result = await db.execute(select(Shift).where(Shift.id == shift_id, Shift.is_active == True))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Active shift not found")
    return shift
from datetime import datetime


async def get_pharmacist_profile(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        # select(User).where(User.id == user_id, User.role == "PHARMACIST")
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Pharmacist not found")
    return user



# async def assign_shift_operation(db, op, current_user):
#
#     # check user exists
#     user = await db.get(User, op.user_id)
#     if not user:
#         raise HTTPException(404, "User not found")
#
#     # ensure pharmacist
#     if user.role != "PHARMACIST":
#         raise HTTPException(400, "User is not pharmacist")
#
#     # check shift exists
#     shift = await db.get(Shift, op.shift_id)
#     if not shift:
#         raise HTTPException(404, "Shift not found")
#
#     # check duplicate assignment
#     existing = await db.execute(
#         select(ShiftAssign).where(
#             ShiftAssign.user_id == op.user_id,
#             ShiftAssign.assigned_date == op.assigned_date
#         )
#     )
#
#     if existing.scalar():
#         raise HTTPException(400, "Shift already assigned for that date")
#
#     # create assignment
#     assignment = ShiftAssign(
#         user_id=op.user_id,
#         shift_id=op.shift_id,
#         assigned_date=op.assigned_date
#     )
#
#     db.add(assignment)
#     await db.commit()
#
#     return {
#         "success": True,
#         "message": "Shift assigned successfully",
#         "shift_id": op.shift_id,
#         "affected_users": [op.user_id]
#     }

async def assign_shift_operation(db, op, current_user):

    # check user exists
    user = await db.get(User, op.user_id)

    if not user:
        raise HTTPException(404, "User not found")

    # ensure pharmacist
    if user.role != "PHARMACIST":
        raise HTTPException(400, "User is not pharmacist")

    # check shift exists
    shift = await db.get(Shift, op.shift_id)

    if not shift:
        raise HTTPException(404, "Shift not found")

    # duplicate check
    existing = await db.execute(
        select(UserShift).where(
            UserShift.user_id == op.user_id,
            UserShift.assigned_date == op.assigned_date
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Shift already assigned for that date"
        )

    # create assignment
    assignment = UserShift(
        user_id=op.user_id,
        shift_id=op.shift_id,
        assigned_date=op.assigned_date
    )

    db.add(assignment)

    await db.commit()
    await db.refresh(assignment)

    return {
        "success": True,
        "message": "Shift assigned successfully",
        "assignment_id": assignment.id,
        "shift_id": op.shift_id,
        "affected_users": [op.user_id]
    }

