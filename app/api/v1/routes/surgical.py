# from fastapi import APIRouter, Depends, HTTPException, Form
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database.user_db import get_db
# from app.schemas.user_schemas import SurgicalItemCreate, SurgicalItemRead, SurgicalBatchCreate, SurgicalBatchRead
# from app.crud.surgical import (
#     create_surgical_item, get_surgical_items, get_surgical_item,
#     create_surgical_batch, get_fefo_surgical_batch, update_surgical_batch_quantity
# )
# from app.crud.stock_ledger import create_stock_ledger_entry
# from app.crud.surgical import get_surgical_item
#
# router = APIRouter(prefix="/surgical-items", tags=["Surgical Items"])
# surgical_batch_router = APIRouter(prefix="/surgical-batches", tags=["Surgical Batches"])
#
# @surgical_batch_router.post("/", response_model=SurgicalBatchRead)
# async def create_surgical_batch_endpoint(
#     batch: SurgicalBatchCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     item = await get_surgical_item(db, batch.surgical_item_id)
#     if not item:
#         raise HTTPException(status_code=404, detail="Surgical item not found")
#     result = await create_surgical_batch(db, batch)
#     return {
#         "message": "Surgical items Successfully Added to System",
#         "stock_ledger_updated": True,
#         "batch": result
#     }
#
# @router.post("/", response_model=SurgicalItemRead)
# async def create_surgical_item_endpoint(
#     item: SurgicalItemCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     return await create_surgical_item(db, item)
#
# @router.get("/", response_model=list[SurgicalItemRead])
# async def list_surgical_items(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db)
# ):
#     return await get_surgical_items(db, skip, limit)
#
# @surgical_batch_router.post("/issue/")
# async def issue_surgical_item(
#     procedure_id: int = Form(...),
#     surgical_item_id: int = Form(...),
#     quantity: int = Form(...),
#     patient_type: str = Form(...),
#     db: AsyncSession = Depends(get_db)
# ):
#     item = await get_surgical_item(db, surgical_item_id)
#     if not item:
#         raise HTTPException(404, "Surgical item not found")
#
#     batch = await get_fefo_surgical_batch(db, surgical_item_id, quantity)
#     if not batch or batch.quantity_available < quantity:
#         raise HTTPException(400, "Insufficient FEFO stock")
#
#     new_qty = batch.quantity_available - quantity
#     await update_surgical_batch_quantity(db, batch.id, new_qty)
#     await create_stock_ledger_entry(
#         db, batch.id, "ISSUE", 0, quantity, new_qty,
#         -quantity * batch.cost_price, f"Issue to {patient_type} procedureid {procedure_id}"
#     )
#     return {
#         "status": "issued",
#         "batch_id": batch.id,
#         "rackshelf": batch.rack_shelf_number,
#         "remaining_qty": new_qty
#     }

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.security import async_get_db, require_roles
from app.models.auth import User
from app.models.entry_models import SurgicalItem, SurgicalBatch
from app.schemas.entry_schemas import (
    SurgicalItemCreate, SurgicalItemRead, SurgicalItemUpdate,
    SurgicalBatchCreate, SurgicalBatchRead, SurgicalBatchUpdate
)
from app.services.surgical import (
    create_surgical_item, get_surgical_items, get_surgical_item,
    update_surgical_item, delete_surgical_item,
    create_surgical_batch, get_surgical_batch, get_surgical_batches,
    update_surgical_batch, delete_surgical_batch
)

# Items Router
router = APIRouter(prefix="/surgical-items", tags=["Surgical Items"])
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@router.post(
    "/",
    response_model=SurgicalItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_surgical_item_endpoint(
    item: SurgicalItemCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("pharmacist", "superadmin")),
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

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
    # Validate item_type
    if item.item_type != "SurgicalItem":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_type must be 'SurgicalItem'."
        )

    try:
        # # Price validation
        # if item.price < 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Price cannot be negative."
        #     )

        # Stock validation
        # if item.stock_quantity < 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Stock quantity cannot be negative."
        #     )

        # Duplicate item name
        existing = await db.execute(
            select(SurgicalItem).where(
                SurgicalItem.item_name == item.item_name,
                SurgicalItem.hospital_id == hospital_id,
                SurgicalItem.branch_id == branch_id,
            )
        )

        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Surgical item already exists."
            )

        # Inject tenant information
        item.hospital_id = hospital_id
        item.branch_id = branch_id

        new_item = await create_surgical_item(db, item)

        return SurgicalItemRead.model_validate(new_item)

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


@router.get("/", response_model=List[SurgicalItemRead])
async def list_surgical_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, le=100),
        search: Optional[str] = None,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    return await get_surgical_items(db, skip, limit, search=search)


@router.get("/{item_id}", response_model=SurgicalItemRead)
async def get_surgical_item_endpoint(
        item_id: int,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    item = await get_surgical_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Surgical item not found")
    return item


from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# @router.put("/{item_id}", response_model=SurgicalItemRead)
# async def update_surgical_item_endpoint(
#     item_id: int,
#     item_update: SurgicalItemUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(require_roles("pharmacist", "superadmin")),
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.current_branch_id
#
#     # Validate user assignment
#     if not hospital_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Hospital is not assigned."
#         )
#
#     if not branch_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Branch is not assigned."
#         )
#
#     try:
#         # Check item exists
#         item = await get_surgical_item(db, item_id)
#
#         if not item:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Surgical item not found."
#             )
#
#         # Optional: Ensure the item belongs to the same hospital & branch
#         if (
#             item.hospital_id != hospital_id or
#             item.branch_id != branch_id
#         ):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You are not authorized to update this surgical item."
#             )
#         #
#         # # Validate price
#         # if item_update.price < 0:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_400_BAD_REQUEST,
#         #         detail="Price cannot be negative."
#         #     )
#
#         # Validate stock
#         # if item_update.stock_quantity < 0:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_400_BAD_REQUEST,
#         #         detail="Stock quantity cannot be negative."
#         #     )
#
#         # Prevent duplicate item names
#         duplicate = await db.execute(
#             select(SurgicalItem).where(
#                 SurgicalItem.item_name == item_update.item_name,
#                 SurgicalItem.hospital_id == hospital_id,
#                 SurgicalItem.branch_id == branch_id,
#                 SurgicalItem.id != item_id,
#             )
#         )
#
#         if duplicate.scalar_one_or_none():
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="A surgical item with this name already exists."
#             )
#
#         # Update
#         duplicate_code = await db.execute(
#             select(SurgicalItem).where(
#                 SurgicalItem.item_code == item_update.item_code,
#                 SurgicalItem.hospital_id == hospital_id,
#                 SurgicalItem.branch_id == branch_id,
#                 SurgicalItem.id != item_id,
#             )
#         )
#
#         if duplicate_code.scalar_one_or_none():
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="A surgical item with this item code already exists."
#             )
#
#         updated = await update_surgical_item(
#             db,
#             item_id,
#             item_update,
#         )
#
#         if not updated:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Unable to update surgical item."
#             )
#
#         return SurgicalItemRead.model_validate(updated)
#
#     except HTTPException:
#         raise
#
#     # except IntegrityError:
#     #     await db.rollback()
#     #     raise HTTPException(
#     #         status_code=status.HTTP_409_CONFLICT,
#     #         detail="Database constraint violation."
#     #     )
#     #
#     # except SQLAlchemyError:
#     #     await db.rollback()
#     #     raise HTTPException(
#     #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#     #         detail="Database error occurred."
#     #     )
#     #
#     # except Exception:
#     #     await db.rollback()
#     #     raise HTTPException(
#     #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#     #         detail="Unexpected server error."
#     #     )

@router.put("/{item_id}", response_model=SurgicalItemRead)
async def update_surgical_item_endpoint(
    item_id: int,
    item_update: SurgicalItemUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("pharmacist", "superadmin")),
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

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
        # Check item exists
        item = await get_surgical_item(db, item_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Surgical item not found."
            )

        # Check ownership
        if (
            item.hospital_id != hospital_id or
            item.branch_id != branch_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this surgical item."
            )

        # Validate required fields
        required_fields = {
            "Item Code": item_update.item_code,
            "Item Name": item_update.item_name,
            "Item Type": item_update.item_type,
            "Sterility Status": item_update.sterility_status,
            "Unit Of Measure": item_update.unit_of_measure,
        }

        for field_name, value in required_fields.items():
            if value is None or not value.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name} cannot be empty."
                )

        if item_update.usage_count_per_procedure <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usage count per procedure must be greater than 0."
            )

        # Check duplicate item name
        duplicate = await db.execute(
            select(SurgicalItem).where(
                SurgicalItem.item_name == item_update.item_name,
                SurgicalItem.hospital_id == hospital_id,
                SurgicalItem.branch_id == branch_id,
                SurgicalItem.id != item_id,
            )
        )

        if duplicate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A surgical item with this name already exists."
            )

        # Check duplicate item code
        duplicate_code = await db.execute(
            select(SurgicalItem).where(
                SurgicalItem.item_code == item_update.item_code,
                SurgicalItem.hospital_id == hospital_id,
                SurgicalItem.branch_id == branch_id,
                SurgicalItem.id != item_id,
            )
        )

        if duplicate_code.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A surgical item with this item code already exists."
            )

        # Update item
        updated = await update_surgical_item(
            db=db,
            item_id=item_id,
            item_update=item_update,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to update surgical item."
            )

        return SurgicalItemRead.model_validate(
            updated,
            from_attributes=True
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.delete("/{item_id}", response_model=dict)
async def delete_surgical_item_endpoint(
        item_id: int,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    success = await delete_surgical_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Surgical item not found")
    return {"message": "Surgical item deleted successfully"}


# Batches Router
surgical_batch_router = APIRouter(prefix="/surgical-batches", tags=["Surgical Batches"])


@surgical_batch_router.post("/", response_model=dict)
async def create_surgical_batch_endpoint(
        batch: SurgicalBatchCreate,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    item = await get_surgical_item(db, batch.surgical_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Surgical item not found")

    result = await create_surgical_batch(db, batch)
    return {
        "message": "Surgical items Successfully Added to System",
        "stock_ledger_updated": True,
        "batch": {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
    }

@surgical_batch_router.get("/", response_model=List[SurgicalBatchRead])
async def list_surgical_batches(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, le=100),
        surgical_item_id: Optional[int] = None,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    return await get_surgical_batches(db, skip, limit, surgical_item_id)


@surgical_batch_router.get("/{batch_id}", response_model=SurgicalBatchRead)
async def get_surgical_batch_endpoint(
        batch_id: int,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin"))
):
    batch = await get_surgical_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Surgical batch not found")
    return batch

from datetime import date
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

@surgical_batch_router.put("/{batch_id}", response_model=SurgicalBatchRead)
async def update_surgical_batch_endpoint(
    batch_id: int,
    batch_update: SurgicalBatchUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles("pharmacist", "superadmin")),
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

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
        # Check batch exists
        existing_batch = await get_surgical_batch(db, batch_id)

        if not existing_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Surgical batch not found."
            )

        # Ensure same hospital/branch
        if (
            existing_batch.hospital_id != hospital_id or
            existing_batch.branch_id != branch_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this surgical batch."
            )

        # Validate surgical item if changed
        if batch_update.surgical_item_id != existing_batch.surgical_item_id:
            item = await get_surgical_item(db, batch_update.surgical_item_id)

            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Surgical item not found."
                )

        # Duplicate batch number
        duplicate = await db.execute(
            select(SurgicalBatch).where(
                SurgicalBatch.batch_number == batch_update.batch_number,
                SurgicalBatch.surgical_item_id == batch_update.surgical_item_id,
                SurgicalBatch.hospital_id == hospital_id,
                SurgicalBatch.branch_id == branch_id,
                SurgicalBatch.id != batch_id,
            )
        )

        if duplicate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Batch number already exists for this surgical item."
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

        # Update
        updated = await update_surgical_batch(
            db,
            batch_id,
            batch_update,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to update surgical batch."
            )

        return SurgicalBatchRead.model_validate(updated)

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

@surgical_batch_router.delete("/{batch_id}", response_model=dict)
async def delete_surgical_batch_endpoint(
        batch_id: int,
        db: AsyncSession = Depends(async_get_db),
        User=Depends(require_roles("pharmacist", "superadmin")),
):
    success = await delete_surgical_batch(db, batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Surgical batch not found")
    return {"message": "Surgical batch deleted successfully"}

#
# @surgical_batch_router.post("/issue/")
# async def issue_surgical_item(
#         procedure_id: int = Form(...),
#         surgical_item_id: int = Form(...),
#         quantity: int = Form(...),
#         patient_type: str = Form(...),
#         db: AsyncSession = Depends(get_db)
# ):
#     item = await get_surgical_item(db, surgical_item_id)
#     if not item:
#         raise HTTPException(404, "Surgical item not found")
#
#     batch = await get_fefo_surgical_batch(db, surgical_item_id, quantity)
#     if not batch or batch.quantity_available < quantity:
#         raise HTTPException(400, "Insufficient FEFO stock")
#
#     new_qty = batch.quantity_available - quantity
#     await update_surgical_batch_quantity(db, batch.id, new_qty)
#     await create_stock_ledger_entry(
#         db, batch.id, "ISSUE", 0, quantity, new_qty,
#         -quantity * batch.cost_price, f"Issue to {patient_type} procedureid {procedure_id}"
#     )
#     return {
#         "status": "issued",
#         "batch_id": batch.id,
#         "rackshelf": batch.rack_shelf_number,
#         "remaining_qty": new_qty
#     }
