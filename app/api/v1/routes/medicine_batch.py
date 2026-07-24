# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List, Optional

# from starlette import status

# from app.database import get_db
# from app.models.user_models import User
# from app.schemas.entry_schemas import BatchCreate, BatchRead, BatchUpdate
# from app.crud.medicine_entry import get_medicine
# from app.crud.medicine_batch import (
#     create_batch,
#     get_batch,
#     get_batches,
#     update_batch,
#     delete_batch,
# )
# from app.utils.ipd_security import get_current_pharmacist
# from app.utils.role_based import role_required


# router = APIRouter(
#     prefix="/medicine_batches",
#     tags=["medicine_batches"],
# )


# # @router.post("/", response_model=BatchRead)
# # async def create_batch_endpoint(
# #     batch: BatchCreate,
# #     db: AsyncSession = Depends(get_db),
# #     pharmacist : User = Depends(role_required("pharmacist")),
# # ):

# #     hospital_id = pharmacist.hospital_id
# #     branch_id = pharmacist.branch_id

# #     # validate medicine within hospital
# #     medicine = await get_medicine(
# #         db,
# #         batch.medicine_id,
# #         hospital_id,
# #         branch_id,
# #     )

# #     if not medicine:
# #         raise HTTPException(404, "Medicine not found")

# #     # attach tenant context

# #     batch.hospital_id = hospital_id
# #     batch.branch_id = branch_id

# #     result = await create_batch(db, batch)

# #     return BatchRead.model_validate(result)

# @router.post(
#     "/",
#     response_model=BatchRead,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_batch_endpoint(
#     batch: BatchCreate,
#     db: AsyncSession = Depends(get_db),
#     pharmacist: User = Depends(role_required("pharmacist")),
# ):
#     """
#     Create a medicine batch (Pharmacist only)
#     """

#     hospital_id = pharmacist.hospital_id
#     branch_id = pharmacist.branch_id

#     # Validate medicine belongs to same tenant
#     medicine = await get_medicine(
#         db=db,
#         medicine_id=batch.medicine_id,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#     )

#     if not medicine:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Medicine not found",
#         )

#     # DO NOT mutate Pydantic model directly
#     batch_data = batch.model_dump()
#     batch_data["hospital_id"] = hospital_id
#     batch_data["branch_id"] = branch_id

#     # Create batch
#     new_batch = await create_batch(db, batch_data)

#     return new_batch


# @router.get("/", response_model=List[BatchRead])
# async def list_batches(
#     db: AsyncSession = Depends(get_db),
#     pharmacist : User = Depends(role_required("pharmacist")),
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, le=100),
#     medicine_id: Optional[int] = Query(None),
#     search: Optional[str] = Query(None),
# ):

#     hospital_id = pharmacist.hospital_id
#     branch_id = pharmacist.branch_id

#     batches = await get_batches(
#         db=db,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         skip=skip,
#         limit=limit,
#         medicine_id=medicine_id,
#         search=search,
#     )

#     return [BatchRead.model_validate(batch) for batch in batches]


# @router.get("/{batch_id}", response_model=BatchRead)
# async def get_batch_endpoint(
#     batch_id: int,
#     db: AsyncSession = Depends(get_db),
#     pharmacist=Depends(get_current_pharmacist),
# ):

#     hospital_id = pharmacist["hospital_id"]
#     branch_id = pharmacist["branch_id"]

#     batch = await get_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#     )

#     if not batch:
#         raise HTTPException(404, "Batch not found")

#     return BatchRead.model_validate(batch)


# @router.put("/{batch_id}", response_model=BatchRead)
# async def update_batch_endpoint(
#     batch_id: int,
#     batch_update: BatchUpdate,
#     db: AsyncSession = Depends(get_db),
#     pharmacist=Depends(get_current_pharmacist),
# ):

#     hospital_id = pharmacist["hospital_id"]
#     branch_id = pharmacist["branch_id"]

#     existing_batch = await get_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#     )

#     if not existing_batch:
#         raise HTTPException(404, "Batch not found")

#     # validate medicine change
#     if (
#         batch_update.medicine_id
#         and batch_update.medicine_id != existing_batch.medicine_id
#     ):
#         medicine = await get_medicine(
#             db,
#             batch_update.medicine_id,
#             hospital_id,
#             branch_id,
#         )

#         if not medicine:
#             raise HTTPException(404, "Medicine not found")

#     updated_batch = await update_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#         batch_update,
#     )

#     return BatchRead.model_validate(updated_batch)


# @router.delete("/{batch_id}", response_model=dict)
# async def delete_batch_endpoint(
#     batch_id: int,
#     db: AsyncSession = Depends(get_db),
#     pharmacist=Depends(get_current_pharmacist),
# ):

#     hospital_id = pharmacist["hospital_id"]
#     branch_id = pharmacist["branch_id"]

#     batch = await get_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#     )

#     if not batch:
#         raise HTTPException(404, "Batch not found")

#     await delete_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#     )

#     return {"message": "Batch deleted successfully"}


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from starlette import status

from app.core.security import async_get_db
from app.models.entry_models import Batch, Medicine
from app.models.auth import User
from app.schemas.entry_schemas import BatchCreate, BatchRead, BatchUpdate
from app.services.medicine_entry import get_medicine
from app.services.medicine_batch import (
    create_batch,
    get_batch,
    get_batches,
    update_batch,
    delete_batch,
)
from app.utils.ipd_security import get_current_pharmacist
from app.core.security import require_roles


router = APIRouter(
    prefix="/medicine_batches",
    tags=["medicine_batches"],
)

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

@router.post(
    "/",
    response_model=BatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_batch_endpoint(
    batch: BatchCreate,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist", "superadmin")),
):
    try:
        # Validate user tenant
        hospital_id = pharmacist.hospital_id
        branch_id = pharmacist.current_branch_id

        if not hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hospital is not assigned to the current user."
            )

        if not branch_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Branch is not assigned to the current user."
            )

        # Validate medicine exists
        medicine = await get_medicine(
            db=db,
            medicine_id=batch.medicine_id,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found."
            )

        # Business validations
        if hasattr(batch, "quantity") and batch.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero."
            )

        if hasattr(batch, "purchase_price") and batch.purchase_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase price cannot be negative."
            )

        if hasattr(batch, "selling_price") and batch.selling_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be negative."
            )

        if (
            hasattr(batch, "purchase_price")
            and hasattr(batch, "selling_price")
            and batch.purchase_price > batch.selling_price
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be less than purchase price."
            )

        if hasattr(batch, "manufacture_date") and batch.manufacture_date:
            if batch.manufacture_date > date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Manufacture date cannot be in the future."
                )

        if hasattr(batch, "expiry_date") and batch.expiry_date:
            if batch.expiry_date <= date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Expiry date must be in the future."
                )

        if (
            hasattr(batch, "manufacture_date")
            and hasattr(batch, "expiry_date")
            and batch.manufacture_date
            and batch.expiry_date
            and batch.manufacture_date >= batch.expiry_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manufacture date must be before expiry date."
            )

        # Duplicate batch check
        if hasattr(batch, "batch_number"):
            existing = await db.execute(
                select(Batch).where(
                    Batch.batch_number == batch.batch_number,
                    Batch.medicine_id == batch.medicine_id,
                    Batch.hospital_id == hospital_id,
                    Batch.branch_id == branch_id,
                )
            )

            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Batch number already exists for this medicine."
                )

        # Prepare data
        batch_data = batch.model_dump()
        batch_data["hospital_id"] = hospital_id
        batch_data["branch_id"] = branch_id

        # Create batch
        new_batch = await create_batch(db, batch_data)

        if not new_batch:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch."
            )

        return BatchRead.model_validate(new_batch)

    except HTTPException:
        raise

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database integrity error: {str(e.orig)}"
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
@router.get("/", response_model=List[BatchRead])
async def list_batches(
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist","superadmin")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    medicine_id: str | None = Query(None),
    search: Optional[str] = Query(None),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.current_branch_id

    # Safely parse medicine_id
    parsed_medicine_id: int | None = None
    if medicine_id and medicine_id.strip():
        try:
            parsed_medicine_id = int(medicine_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="medicine_id must be a valid integer")

    query = (
        select(Batch)
        .join(Medicine, Batch.medicine_id == Medicine.id)  # ← join Medicine
        .where(
            and_(
                Batch.hospital_id == hospital_id,
                Batch.branch_id == branch_id,
            )
        )
    )

    if parsed_medicine_id:
        query = query.where(Batch.medicine_id == parsed_medicine_id)

    if search:
        term = search.strip().lower()
        query = query.where(
            or_(
                func.lower(Batch.batch_number).like(f"%{term}%"),
                func.lower(Batch.vendor_name).like(f"%{term}%"),
                func.lower(Batch.strength).like(f"%{term}%"),
                func.lower(Medicine.item_name).like(f"%{term}%"),
                func.lower(Medicine.generic_name).like(f"%{term}%"),
                func.lower(Medicine.brand_name).like(f"%{term}%"),
            )
        )

    query = query.offset(skip).limit(limit).order_by(Batch.id.desc())
    result = await db.execute(query)
    batches = result.scalars().all()

    return [BatchRead.model_validate(batch) for batch in batches]


@router.get("/{batch_id}", response_model=BatchRead)
async def get_batch_endpoint(
    batch_id: int,
    db: AsyncSession = Depends(async_get_db),
    pharmacist=Depends(get_current_pharmacist),
):

    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.current_branch_id

    batch = await get_batch(
        db,
        hospital_id,
        branch_id,
        batch_id,
    )

    if not batch:
        raise HTTPException(404, "Batch not found")

    return BatchRead.model_validate(batch)


# @router.put("/{batch_id}", response_model=BatchRead)
# async def update_batch_endpoint(
#     batch_id: int,
#     batch_update: BatchUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     pharmacist=Depends(get_current_pharmacist),
# ):
#
#     hospital_id = pharmacist.hospital_id
#     branch_id = pharmacist.current_branch_id
#
#     # print("hospital:", pharmacist.hospital_id)
#     # print("branch:", pharmacist.current_branch_id)
#     # print(vars(pharmacist))
#
#     existing_batch = await get_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#     )
#
#     if not existing_batch:
#         raise HTTPException(404, "Batch not found")
#
#     # Validate medicine change if medicine_id is being updated
#     if (
#         batch_update.medicine_id
#         and batch_update.medicine_id != existing_batch.medicine_id
#     ):
#         medicine = await get_medicine(
#             db,
#             batch_update.medicine_id,
#             hospital_id,
#             branch_id,
#         )
#
#         if not medicine:
#             raise HTTPException(404, "Medicine not found")
#
#     updated_batch = await update_batch(
#         db,
#         hospital_id,
#         branch_id,
#         batch_id,
#         batch_update,
#     )
#
#     return BatchRead.model_validate(updated_batch)
#
from datetime import date
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@router.put("/{batch_id}", response_model=BatchRead)
async def update_batch_endpoint(
    batch_id: int,
    batch_update: BatchUpdate,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(get_current_pharmacist),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.current_branch_id

    # Validate pharmacist
    if not hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital is not assigned."
        )

    if not branch_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Branch is not assigned."
        )

    try:
        # Check batch exists
        existing_batch = await get_batch(
            db,
            hospital_id,
            branch_id,
            batch_id,
        )

        if not existing_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found."
            )

        # Validate medicine exists if changed
        if batch_update.medicine_id != existing_batch.medicine_id:
            medicine = await get_medicine(
                db,
                batch_update.medicine_id,
                hospital_id,
                branch_id,
            )

            if not medicine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medicine not found."
                )

        # Duplicate batch number
        duplicate = await db.execute(
            select(Batch).where(
                Batch.batch_number == batch_update.batch_number,
                Batch.medicine_id == batch_update.medicine_id,
                Batch.hospital_id == hospital_id,
                Batch.branch_id == branch_id,
                Batch.id != batch_id,
            )
        )

        if duplicate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch number already exists."
            )

        # Quantity validation
        if batch_update.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero."
            )

        # Price validation
        if batch_update.purchase_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase price cannot be negative."
            )

        if batch_update.selling_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be negative."
            )

        if batch_update.purchase_price > batch_update.selling_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be less than purchase price."
            )

        # Date validation
        if batch_update.manufacture_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manufacture date cannot be in the future."
            )

        if batch_update.expiry_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiry date must be in the future."
            )

        if batch_update.manufacture_date >= batch_update.expiry_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manufacture date must be before expiry date."
            )

        # Update batch
        updated_batch = await update_batch(
            db,
            hospital_id,
            branch_id,
            batch_id,
            batch_update,
        )

        if not updated_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found."
            )

        return BatchRead.model_validate(updated_batch)

    except HTTPException:
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database constraint violation."
        )

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred."
        )

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error."
        )

@router.delete("/{batch_id}", response_model=dict)
async def delete_batch_endpoint(
    batch_id: int,
    db: AsyncSession = Depends(async_get_db),
    pharmacist=Depends(get_current_pharmacist),
):

    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.branch_id

    batch = await get_batch(
        db,
        hospital_id,
        branch_id,
        batch_id,
    )

    if not batch:
        raise HTTPException(404, "Batch not found")

    await delete_batch(
        db,
        hospital_id,
        branch_id,
        batch_id,
    )

    return {"message": "Batch deleted successfully"}