from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.security import async_get_db

from app.models.auth import User
from app.models.entry_models import NonSurgicalItem, NonSurgicalBatch
from app.schemas.entry_schemas import (
    NonSurgicalItemCreate,
    NonSurgicalItemRead,
    NonSurgicalItemUpdate,
    NonSurgicalBatchCreate,
    NonSurgicalBatchRead,
    NonSurgicalBatchUpdate,
)

from app.services.non_surgical import (
    create_non_surgical_item,
    get_non_surgical_item,
    get_non_surgical_items,
    update_non_surgical_item,
    delete_non_surgical_item,
    create_non_surgical_batch_crud,
    get_non_surgical_batches,
    get_non_surgical_batch,
    update_non_surgical_batch,
    delete_non_surgical_batch_db,
)
from app.core.security import require_roles


non_surgical_item_router = APIRouter(
    prefix="/non-surgical-items",
    tags=["Non-Surgical Items"],
)



# @non_surgical_item_router.post("/", response_model=NonSurgicalItemRead)
# async def create_item(
#     item: NonSurgicalItemCreate,
#     db: AsyncSession = Depends(async_get_db),
#     pharmacist: User = Depends(require_roles("pharmacist","superadmin")),
# ):
#
#     if not pharmacist.hospital_id or not pharmacist.current_branch_id:
#         raise HTTPException(
#             status_code=400,
#             detail="User not assigned to hospital/branch"
#         )
#
#     return await create_non_surgical_item(
#         db=db,
#         item=item,
#         hospital_id=pharmacist.hospital_id,
#         branch_id=pharmacist.current_branch_id,
#     )
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@non_surgical_item_router.post(
    "/",
    response_model=NonSurgicalItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    item: NonSurgicalItemCreate,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist", "superadmin")),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.current_branch_id

    # Validate hospital & branch
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
        # Validate item name
        if not item.item_name or not item.item_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item name is required."
            )

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
@non_surgical_item_router.get("/", response_model=List[NonSurgicalItemRead])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
):
    return await get_non_surgical_items(
        db=db,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        skip=skip,
        limit=limit,
        search=search,
    )


# @non_surgical_item_router.get("/{item_id}", response_model=NonSurgicalItemRead)
# async def get_item(
#     item_id: int,
#     db: AsyncSession = Depends(get_db),
# ):
#     item = await get_non_surgical_item(db, item_id)

#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")

#     return item
non_surgical_batch_router = APIRouter(
    prefix="/non-surgical-batches",
    tags=["Non-Surgical Batches"],
)

@non_surgical_item_router.get("/{item_id}", response_model=NonSurgicalItemRead)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist","superadmin")),
):

    item = await get_non_surgical_item(
        db=db,
        item_id=item_id,
        hospital_id=pharmacist.hospital_id,
        branch_id=pharmacist.current_branch_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    return item

#
# @non_surgical_item_router.put("/{item_id}", response_model=NonSurgicalItemRead)
# async def update_item(
#     item_id: int,
#     item_update: NonSurgicalItemUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     user: User = Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
# ):
#     updated = await update_non_surgical_item(
#         db=db,
#         item_id=item_id,
#         item_update=item_update,
#         hospital_id=user.hospital_id,
#         branch_id=user.current_branch_id,
#     )
#
#     if not updated:
#         raise HTTPException(status_code=404, detail="Item not found")
#
#     return updated
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@non_surgical_item_router.put("/{item_id}", response_model=NonSurgicalItemRead)
async def update_item(
    item_id: int,
    item_update: NonSurgicalItemUpdate,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"])),
):
    hospital_id = user.hospital_id
    branch_id = user.current_branch_id

    # Validate hospital & branch assignment
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
        # Check if item exists
        existing_item = await get_non_surgical_item(
            db=db,
            item_id=item_id,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found."
            )

        # Validate item name
        if not item_update.item_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item name cannot be empty."
            )

        # Validate price
        if item_update.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price cannot be negative."
            )

        # Validate stock
        if item_update.stock_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock quantity cannot be negative."
            )

        # Validate reorder level (if present)
        if hasattr(item_update, "reorder_level") and item_update.reorder_level < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reorder level cannot be negative."
            )

        # Duplicate item name check
        duplicate = await db.execute(
            select(NonSurgicalItem).where(
                NonSurgicalItem.item_name == item_update.item_name,
                NonSurgicalItem.hospital_id == hospital_id,
                NonSurgicalItem.branch_id == branch_id,
                NonSurgicalItem.id != item_id,
            )
        )

        if duplicate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An item with this name already exists."
            )

        # Update item
        updated = await update_non_surgical_item(
            db=db,
            item_id=item_id,
            item_update=item_update,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to update item."
            )

        return NonSurgicalItemRead.model_validate(updated)

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

@non_surgical_item_router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
):
    success = await delete_non_surgical_item(
        db=db,
        item_id=item_id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"message": "Item deleted successfully"}

# @non_surgical_batch_router.post("/", response_model=NonSurgicalBatchRead)
# async def create_batch(
#     batch: NonSurgicalBatchCreate,
#     db: AsyncSession = Depends(get_db),
# ):
#     item = await get_non_surgical_item(db, batch.non_surgical_item_id)

#     if not item:
#         raise HTTPException(
#             status_code=404,
#             detail="Non-surgical item not found",
#         )

#     return await create_non_surgical_batch_crud(db, batch)

# @non_surgical_batch_router.post("/", response_model=NonSurgicalBatchRead)
# async def create_batch(
#     batch: NonSurgicalBatchCreate,
#     db: AsyncSession = Depends(async_get_db),
#     pharmacist: User = Depends(require_roles("pharmacist","superadmin")),
# ):
#
#     item = await get_non_surgical_item(
#         db=db,
#         item_id=batch.non_surgical_item_id,
#         hospital_id=pharmacist.hospital_id,
#         branch_id=pharmacist.current_branch_id,
#     )
#
#     if not item:
#         raise HTTPException(
#             status_code=404,
#             detail="Non-surgical item not found",
#         )
#
#     return await create_non_surgical_batch_crud(
#         db=db,
#         batch=batch,
#         hospital_id=pharmacist.hospital_id,
#         branch_id=pharmacist.current_branch_id,
#     )
from datetime import date
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@non_surgical_batch_router.post(
    "/",
    response_model=NonSurgicalBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_batch(
    batch: NonSurgicalBatchCreate,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist", "superadmin")),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.current_branch_id

    # Validate hospital & branch
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


        # Validate item exists
        item = await get_non_surgical_item(
            db=db,
            item_id=batch.non_surgical_item_id,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Non-surgical item not found."
            )

        # Duplicate batch number
        duplicate = await db.execute(
            select(NonSurgicalBatch).where(
                NonSurgicalBatch.batch_number == batch.batch_number,
                NonSurgicalBatch.non_surgical_item_id == batch.non_surgical_item_id,
                NonSurgicalBatch.hospital_id == hospital_id,
                NonSurgicalBatch.branch_id == branch_id,
            )
        )

        if duplicate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch number already exists."
            )

        # Quantity validation
        if batch.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero."
            )

        # Price validation
        if batch.purchase_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase price cannot be negative."
            )

        if batch.selling_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be negative."
            )

        if batch.purchase_price > batch.selling_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be less than purchase price."
            )

        # Date validation
        if batch.manufacture_date > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manufacture date cannot be in the future."
            )

        if batch.expiry_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiry date must be in the future."
            )

        if batch.manufacture_date >= batch.expiry_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manufacture date must be before expiry date."
            )

        created_batch = await create_non_surgical_batch_crud(
            db=db,
            batch=batch,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        return NonSurgicalBatchRead.model_validate(created_batch)
    #
    # except HTTPException:
    #     raise
    #
    # except IntegrityError:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail="Database constraint violation."
    #     )
    #
    # except SQLAlchemyError:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Database error occurred."
    #     )
    #
    # except Exception:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Unexpected server error."
    #     )

@non_surgical_batch_router.get("/", response_model=List[NonSurgicalBatchRead])
async def list_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    non_surgical_item_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    return await get_non_surgical_batches(
        db=db,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        skip=skip,
        limit=limit,
        non_surgical_item_id=non_surgical_item_id,
    )


@non_surgical_batch_router.get("/{batch_id}", response_model=NonSurgicalBatchRead)
async def get_batch(
    batch_id: int,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    batch = await get_non_surgical_batch(
        db=db,
        batch_id=batch_id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
    )

    if not batch:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    return batch

#
# @non_surgical_batch_router.put(
#     "/{batch_id}",
#     response_model=NonSurgicalBatchRead
# )
# async def update_batch(
#     batch_id: int,
#     batch_update: NonSurgicalBatchUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     user: User = Depends(
#         require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"])
#     ),
# ):
#
#     existing_batch = await get_non_surgical_batch(
#         db=db,
#         batch_id=batch_id,
#         hospital_id=user.hospital_id,
#         branch_id=user.current_branch_id,
#     )
#
#     if not existing_batch:
#         raise HTTPException(
#             status_code=404,
#             detail="Batch not found"
#         )
#
#     if (
#         batch_update.non_surgical_item_id
#         and batch_update.non_surgical_item_id
#         != existing_batch.non_surgical_item_id
#     ):
#
#         item = await get_non_surgical_item(
#             db=db,
#             item_id=batch_update.non_surgical_item_id,
#             hospital_id=user.hospital_id,
#             branch_id=user.current_branch_id,
#         )
#
#         if not item:
#             raise HTTPException(
#                 status_code=404,
#                 detail="Non-surgical item not found",
#             )
#
#     updated = await update_non_surgical_batch(
#         db=db,
#         batch_id=batch_id,
#         batch_update=batch_update,
#         hospital_id=user.hospital_id,
#         branch_id=user.current_branch_id,
#     )
#
#     return updated
from datetime import date
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@non_surgical_batch_router.put(
    "/{batch_id}",
    response_model=NonSurgicalBatchRead
)
async def update_batch(
    batch_id: int,
    batch_update: NonSurgicalBatchUpdate,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(
        require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"])
    ),
):
    hospital_id = user.hospital_id
    branch_id = user.current_branch_id

    # Validate hospital & branch
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


        # Check batch exists
        existing_batch = await get_non_surgical_batch(
            db=db,
            batch_id=batch_id,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not existing_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found."
            )

        # Validate item if changed
        if (
            batch_update.non_surgical_item_id
            != existing_batch.non_surgical_item_id
        ):
            item = await get_non_surgical_item(
                db=db,
                item_id=batch_update.non_surgical_item_id,
                hospital_id=hospital_id,
                branch_id=branch_id,
            )

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Non-surgical item not found."
                )

        # Duplicate batch number
        duplicate = await db.execute(
            select(NonSurgicalBatch).where(
                NonSurgicalBatch.batch_number == batch_update.batch_number,
                NonSurgicalBatch.non_surgical_item_id == batch_update.non_surgical_item_id,
                NonSurgicalBatch.hospital_id == hospital_id,
                NonSurgicalBatch.branch_id == branch_id,
                NonSurgicalBatch.id != batch_id,
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

        # Purchase price validation
        if batch_update.purchase_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase price cannot be negative."
            )

        # Selling price validation
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
        updated = await update_non_surgical_batch(
            db=db,
            batch_id=batch_id,
            batch_update=batch_update,
            hospital_id=hospital_id,
            branch_id=branch_id,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to update batch."
            )

        return NonSurgicalBatchRead.model_validate(updated)

    # except HTTPException:
    #     raise
    #
    # except IntegrityError:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail="Database constraint violation."
    #     )
    #
    # except SQLAlchemyError:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Database error occurred."
    #     )
    #
    # except Exception:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Unexpected server error."
    #     )

@non_surgical_batch_router.delete("/{batch_id}")
async def delete_batch(
    batch_id: int,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(
        require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"])
    ),
):

    success = await delete_non_surgical_batch_db(
        db=db,
        batch_id=batch_id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    return {"message": "Batch deleted successfully"}