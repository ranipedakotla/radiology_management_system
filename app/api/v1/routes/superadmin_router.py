# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from typing import List
# from app.database import get_db
# from app.models.user_models import User
# from app.schemas.rolebased_schemas import UserOut, UserCreate
# from app.utils.rolebased_security import role_required, get_password_hash
from aiosmtplib import status
# router = APIRouter()

# @router.get("/users", response_model=List[UserOut])
# async def list_all_users(db: AsyncSession = Depends(get_db),current_user: User = Depends(role_required(["SUPERADMIN"]))):
#     res = await db.execute(select(User).where(User.is_active == True))
#     return res.scalars().all()

# @router.post("/admins", response_model=UserOut)
# async def create_admin(payload: UserCreate,db: AsyncSession = Depends(get_db),current_user: User = Depends(role_required(["SUPERADMIN"]))):
#     res = await db.execute(select(User).where(User.username == payload.username))
#     if res.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Username already registered")

#     user = User(
#         username=payload.username,
#         email=payload.email,
#         role="ADMIN",
#         hashed_password=get_password_hash(payload.password),
#         is_active=True
#     )
#     db.add(user)
#     await db.commit()
#     await db.refresh(user)
#     return user

# @router.delete("/admins/{admin_id}")
# async def delete_admin(admin_id: int,db: AsyncSession = Depends(get_db),current_user: User = Depends(role_required(["SUPERADMIN"]))):
#     res = await db.execute(
#         select(User).where(User.id == admin_id, User.role == "ADMIN")
#     )
#     admin = res.scalar_one_or_none()
#     if not admin:
#         raise HTTPException(status_code=404, detail="Admin not found")

#     await db.delete(admin)
#     await db.commit()
#     return {"detail": "Admin deleted successfully"}

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.security import async_get_db
from app.models.auth import User
from app.schemas.hospital_schemas import HospitalBranch, Hospital
from app.schemas.rolebased_schemas import UserOut, UserCreate
from app.core.security import require_roles, hash_password,get_current_user


router = APIRouter(prefix="/rbac")


@router.get("/users", response_model=List[UserOut])
async def list_all_users(
    hospital_id: int | None = Query(default=None),
    branch_id: int | None = Query(default=None),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin"]))
):
    query = select(User).where(User.is_active == True)

    # Optional filtering
    if hospital_id:
        query = query.where(User.hospital_id == hospital_id)

    if branch_id:
        query = query.where(User.current_branch_id == branch_id)

    res = await db.execute(query)
    return res.scalars().all()



@router.post("/admins", response_model=UserOut)
async def create_admin(
    payload: UserCreate,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin"]))
):

    # Hospital exists
    hospital = await db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found."
        )

    # Branch exists
    branch = await db.get(HospitalBranch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found."
        )

    # Branch belongs to hospital
    if branch.hospital_id != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch does not belong to the selected hospital."
        )

    # Hospital active
    if not hospital.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital is inactive."
        )

    # Branch active
    if not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch is inactive."
        )

    # Username exists
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists."
        )

    # Email exists
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists."
        )

    # User already admin in same branch (optional)
    result = await db.execute(
        select(User).where(
            User.email == payload.email,
            User.current_branch_id == branch_id,
            User.role == "ADMIN"
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin already exists in this branch."
        )

    user = User(
        username=payload.username,
        email=payload.email,
        role="ADMIN",
        hospital_id=hospital_id,
        current_branch_id=branch_id,
        password_hash=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin"]))
):
    res = await db.execute(
        select(User).where(
            User.id == admin_id,
            User.role == "ADMIN",
            User.hospital_id == hospital_id,
            User.current_branch_id == branch_id
        )
    )

    admin = res.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found in this hospital/branch"
        )

    await db.delete(admin)
    await db.commit()

    return {"detail": "Admin deleted successfully"}

# @router.post("/pharmacists", response_model=UserOut)
# async def create_pharmacist(
#     payload: UserCreate,
#     # hospital_id: int,
#     # branch_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(role_required(["SUPERADMIN"]))
# ):
#     # Check username already exists
#     res = await db.execute(
#         select(User).where(User.username == payload.username)
#     )

#     if res.scalar_one_or_none():
#         raise HTTPException(
#             status_code=400,
#             detail="Username already registered"
#         )

#     pharmacist = User(
#         username=payload.username,
#         email=payload.email,
#         role="PHARMACIST",  
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         hashed_password=get_password_hash(payload.password),
#         is_active=True
#     )

#     db.add(pharmacist)
#     await db.commit()
#     await db.refresh(pharmacist)

#     return pharmacist

@router.post("/pharmacists", response_model=UserOut)
async def create_pharmacist(
    payload: UserCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("superadmin", "admin"))
):

    # Hospital exists
    hospital = await db.get(Hospital, payload.hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found."
        )

    # Hospital active
    if not hospital.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital is inactive."
        )

    # Branch exists
    branch = await db.get(HospitalBranch, payload.current_branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found."
        )

    # Branch belongs to hospital
    if branch.hospital_id != payload.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch does not belong to the selected hospital."
        )

    # Branch active
    if not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch is inactive."
        )

    # Username already exists
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered."
        )

    # Email already exists
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    # Pharmacist already exists in the branch (optional)
    result = await db.execute(
        select(User).where(
            User.email == payload.email,
            User.current_branch_id == payload.current_branch_id,
            User.role == "PHARMACIST"
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pharmacist already exists in this branch."
        )

    pharmacist = User(
        username=payload.username,
        email=payload.email,
        role="PHARMACIST",
        hospital_id=payload.hospital_id,
        current_branch_id=payload.current_branch_id,
        password_hash=hash_password(payload.password),
        is_active=True
    )

    db.add(pharmacist)
    await db.commit()
    await db.refresh(pharmacist)

    return pharmacist

@router.delete("/pharmacists/{pharmacist_id}")
async def delete_pharmacist(
    pharmacist_id: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin","admin"]))
):
    res = await db.execute(
        select(User).where(
            User.id == pharmacist_id,
            User.role == "PHARMACIST",
            User.hospital_id == hospital_id,
            User.current_branch_id == branch_id
        )
    )

    pharmacist = res.scalar_one_or_none()

    if not pharmacist:
        raise HTTPException(
            status_code=404,
            detail="Pharmacist not found in this hospital/branch"
        )

    await db.delete(pharmacist)
    await db.commit()

    return {"detail": "Pharmacist deleted successfully"}


@router.post("/lab-techs", response_model=UserOut)
async def create_lab_tech(
    payload: UserCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin", "admin"]))
):

    # Hospital exists
    hospital = await db.get(Hospital, payload.hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found."
        )

    # Hospital active
    if not hospital.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital is inactive."
        )

    # Branch exists
    branch = await db.get(HospitalBranch, payload.current_branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found."
        )

    # Branch belongs to hospital
    if branch.hospital_id != payload.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch does not belong to the selected hospital."
        )

    # Branch active
    if not branch.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch is inactive."
        )

    # Username already exists
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered."
        )

    # Email already exists
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered."
        )

    # Lab Technician already exists in the same branch (optional)
    result = await db.execute(
        select(User).where(
            User.email == payload.email,
            User.current_branch_id == payload.current_branch_id,
            User.role == "LAB_TECH"
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lab Technician already exists in this branch."
        )

    lab_tech = User(
        username=payload.username,
        email=payload.email,
        role="LAB_TECH",
        hospital_id=payload.hospital_id,
        current_branch_id=payload.current_branch_id,
        password_hash=hash_password(payload.password),
        is_active=True
    )

    db.add(lab_tech)
    await db.commit()
    await db.refresh(lab_tech)

    return lab_tech

@router.delete("/lab-techs/{user_id}")
async def delete_lab_tech(
    user_id: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin","admin"]))
):

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.role == "lab_tech",
            User.hospital_id == hospital_id,
            User.current_branch_id == branch_id
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Lab Technician not found"
        )

    await db.delete(user)
    await db.commit()

    return {"message": "Lab Technician deleted successfully"}

@router.post("/blood-bank-staff", response_model=UserOut)
async def create_blood_bank_staff(
    payload: UserCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin", "admin"]))
):

    # Hospital exists
    hospital = await db.get(Hospital, payload.hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found."
        )

    # Hospital is active
    if not hospital.is_active:
        raise HTTPException(
            status_code=400,
            detail="Hospital is inactive."
        )

    # Branch exists
    branch = await db.get(HospitalBranch, payload.current_branch_id)
    if not branch:
        raise HTTPException(
            status_code=404,
            detail="Branch not found."
        )

    # Branch belongs to hospital
    if branch.hospital_id != payload.hospital_id:
        raise HTTPException(
            status_code=400,
            detail="Branch does not belong to the specified hospital."
        )

    # Branch is active
    if not branch.is_active:
        raise HTTPException(
            status_code=400,
            detail="Branch is inactive."
        )

    # Username already exists
    result = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Username already registered."
        )

    # Email already exists
    result = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    # Blood Bank Staff already exists in this branch (Optional)
    result = await db.execute(
        select(User).where(
            User.email == payload.email,
            User.current_branch_id == payload.current_branch_id,
            User.role == "blood_bank_staff"
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Blood Bank Staff already exists in this branch."
        )

    # Create Blood Bank Staff
    staff = User(
        username=payload.username,
        email=payload.email,
        role="blood_bank_staff",
        hospital_id=payload.hospital_id,
        current_branch_id=payload.current_branch_id,
        password_hash=hash_password(payload.password),
        is_active=True
    )

    db.add(staff)
    await db.commit()
    await db.refresh(staff)

    return staff

@router.delete("/blood-bank-staff/{user_id}")
async def delete_blood_bank_staff(
    user_id: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["superadmin","admin"]))
):

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.role == "blood_bank_staff",
            User.hospital_id == hospital_id,
            User.current_branch_id == branch_id
        )
    )

    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="Blood Bank Staff not found"
        )

    await db.delete(staff)
    await db.commit()

    return {"message": "Blood Bank Staff deleted successfully"}