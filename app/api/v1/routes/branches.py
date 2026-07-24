from aiosmtplib import status
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


from app.models.org import (
    Branch as HospitalBranchModel,
    Hospital as HospitalModel,
)
from app.schemas.hospital_schemas import (
    HospitalBranch,
    HospitalBranchCreate,
)
from app.core.security import async_get_db, require_roles

router = APIRouter(prefix="/branches", tags=["Branches"])



# @router.post("/", response_model=HospitalBranch)
# async def create_branch(
#     branch: HospitalBranchCreate,
#     db: AsyncSession = Depends(get_db),
# ):
#     """Create branch - auto-links to the single main hospital"""
#
#     result = await db.execute(select(HospitalModel))
#     hospital = result.scalars().first()
#
#     if not hospital:
#         raise HTTPException(404, "Main hospital not configured first")
#
#     db_branch = HospitalBranchModel(
#         hospital_id=hospital.id,
#         **branch.model_dump()
#     )
#
#     db.add(db_branch)
#     await db.commit()
#     await db.refresh(db_branch)
#
#     return db_branch


@router.post("/", response_model=HospitalBranch)
async def create_branch(
        branch: HospitalBranchCreate,
        db: AsyncSession = Depends(async_get_db),
        current_user=Depends(require_roles(["superadmin"]))
):
    # Check if main hospital exists
    result = await db.execute(select(HospitalModel))
    hospital = result.scalars().first()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Main hospital not configured first."
        )

    # Check duplicate branch name
    result = await db.execute(
        select(HospitalBranchModel).where(
            HospitalBranchModel.name == branch.name
        )
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch name already exists."
        )

    # Check duplicate branch code
    result = await db.execute(
        select(HospitalBranchModel).where(
            HospitalBranchModel.code == branch.code
        )
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch code already exists."
        )

    # Optional: Check duplicate contact number
    result = await db.execute(
        select(HospitalBranchModel).where(
            HospitalBranchModel.contact_number == branch.contact_number
        )
    )

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact number already exists."
        )

    db_branch = HospitalBranchModel(
        hospital_id=hospital.id,
        name=branch.name,
        code=branch.code,
        location=branch.location,
        contact_number=branch.contact_number,
    )

    db.add(db_branch)
    await db.commit()
    await db.refresh(db_branch)

    return db_branch


@router.get("/", response_model=List[HospitalBranch])
async def list_branches(
    db: AsyncSession = Depends(async_get_db),current_user=Depends(require_roles(["superadmin"]))
):
    """List all branches"""

    result = await db.execute(select(HospitalBranchModel))
    branches = result.scalars().all()

    return branches



@router.get("/{branch_id}", response_model=HospitalBranch)
async def get_branch(
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),current_user=Depends(require_roles(["superadmin"]))
):

    result = await db.execute(
        select(HospitalBranchModel).where(
            HospitalBranchModel.id == branch_id
        )
    )

    branch = result.scalars().first()

    if not branch:
        raise HTTPException(404, "Branch not found")

    return branch




@router.put("/{branch_id}", response_model=HospitalBranch)
async def update_branch(
        branch_id: int,
        branch: HospitalBranchCreate,
        db: AsyncSession = Depends(async_get_db),
        current_user=Depends(require_roles(["superadmin"]))
):
    try:
        result = await db.execute(
            select(HospitalBranchModel).where(
                HospitalBranchModel.id == branch_id
            )
        )

        db_branch = result.scalars().first()

        if not db_branch:
            raise HTTPException(
                status_code=404,
                detail="Branch not found."
            )

        for key, value in branch.model_dump().items():
            setattr(db_branch, key, value)

        await db.commit()
        await db.refresh(db_branch)

        return db_branch

    except IntegrityError as e:
        await db.rollback()

        error = str(e.orig).lower()

        if "duplicate entry" in error:

            if "name" in error:
                raise HTTPException(
                    status_code=409,
                    detail="Branch name already exists."
                )

            elif "code" in error:
                raise HTTPException(
                    status_code=409,
                    detail="Branch code already exists."
                )

            elif "contact_number" in error:
                raise HTTPException(
                    status_code=409,
                    detail="Contact number already exists."
                )

            else:
                raise HTTPException(
                    status_code=409,
                    detail="Duplicate record already exists."
                )

        elif "foreign key constraint fails" in error:
            raise HTTPException(
                status_code=400,
                detail="Invalid reference. Related record does not exist."
            )

        elif "cannot be null" in error:
            raise HTTPException(
                status_code=400,
                detail="One or more required fields are missing."
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Database integrity error."
            )

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error occurred."
        )

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred."
        )


@router.delete("/{branch_id}", status_code=204)
async def delete_branch(
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),current_user=Depends(require_roles(["superadmin"]))
):

    result = await db.execute(
        select(HospitalBranchModel).where(
            HospitalBranchModel.id == branch_id
        )
    )

    db_branch = result.scalars().first()

    if not db_branch:
        raise HTTPException(404, "Branch not found")

    await db.delete(db_branch)
    await db.commit()

    return None