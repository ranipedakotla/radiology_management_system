# from typing import List, Optional
# from datetime import date
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from datetime import datetime, timedelta
# from app.models.entry_models import PharmacyIssue



# async def create_pharmacy_issue(
#     db: AsyncSession,
#     *,
#     hospital_id: int,
#     branch_id: int,
#     item_type: str,
#     item_id: int,
#     batch_type: str,
#     batch_id: int,
#     patient_type: str,
#     reference_id: int,
#     quantity: int,
#     rate_per_unit: float,
#     issue_value: float,
#     issued_by: str
# ) -> PharmacyIssue:

#     issue = PharmacyIssue(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         item_type=item_type,
#         item_id=item_id,
#         batch_type=batch_type,
#         batch_id=batch_id,
#         patient_type=patient_type,
#         reference_id=reference_id,
#         quantity=quantity,
#         rate_per_unit=rate_per_unit,
#         issue_value=issue_value,
#         issued_by=issued_by,
#         is_cancelled=False
#     )

#     db.add(issue)
#     await db.flush()
#     return issue

# async def get_pharmacy_issue(
#     db: AsyncSession,
#     issue_id: int,
#     hospital_id: int,
#     branch_id: int
# ):
#     result = await db.execute(
#         select(PharmacyIssue).where(
#             PharmacyIssue.id == issue_id,
#             PharmacyIssue.hospital_id == hospital_id,
#             PharmacyIssue.branch_id == branch_id,
#             PharmacyIssue.is_cancelled == False
#         )
#     )

#     return result.scalar_one_or_none()



# async def list_pharmacy_issues(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     item_type: Optional[str] = None,
#     reference_id: Optional[int] = None,
#     patient_type: Optional[str] = None,
#     start_date: Optional[date] = None,
#     end_date: Optional[date] = None,
#     limit: int = 100,
#     offset: int = 0,
# ) -> List[PharmacyIssue]:

#     # ✅ safety limit
#     limit = min(limit, 200)

#     query = select(PharmacyIssue).where(
#         PharmacyIssue.hospital_id == hospital_id,
#         PharmacyIssue.branch_id == branch_id,
#         PharmacyIssue.is_cancelled.is_(False),
#     )

#     # ✅ filters
#     if item_type:
#         query = query.where(PharmacyIssue.item_type == item_type)

#     if reference_id:
#         query = query.where(PharmacyIssue.reference_id == reference_id)

#     if patient_type:
#         query = query.where(PharmacyIssue.patient_type == patient_type)

#     # ✅ date filters
#     if start_date:
#         query = query.where(
#             PharmacyIssue.issued_at >= datetime.combine(
#                 start_date, datetime.min.time()
#             )
#         )

#     if end_date:
#         query = query.where(
#             PharmacyIssue.issued_at < datetime.combine(
#                 end_date + timedelta(days=1),
#                 datetime.min.time(),
#             )
#         )

#     # ✅ pagination + sorting
#     query = (
#         query.order_by(PharmacyIssue.issued_at.desc())
#         .limit(limit)
#         .offset(offset)
#     )

#     result = await db.execute(query)
#     return result.scalars().all()

# async def cancel_pharmacy_issue(
#     db: AsyncSession,
#     issue_id: int,
#     hospital_id: int,
#     branch_id: int
# ):

#     issue = await get_pharmacy_issue(
#         db,
#         issue_id,
#         hospital_id,
#         branch_id
#     )

#     if not issue:
#         return False

#     issue.is_cancelled = True
#     await db.flush()
#     return True


from typing import List, Optional
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entry_models import PharmacyIssue


async def create_pharmacy_issue(
    db: AsyncSession,
    *,
    hospital_id: int,
    branch_id: int,
    item_type: str,
    item_id: int,
    batch_type: str,
    batch_id: int,
    patient_type: str,
    reference_id: int,
    quantity: int,
    rate_per_unit: float,
    issue_value: float,
    issued_by: str,
    pharmacist_id: int

) -> PharmacyIssue:

    issue = PharmacyIssue(
        hospital_id=hospital_id,
        branch_id=branch_id,
        item_type=item_type,
        item_id=item_id,
        batch_type=batch_type,
        batch_id=batch_id,
        patient_type=patient_type,
        reference_id=reference_id,
        quantity=quantity,
        rate_per_unit=rate_per_unit,
        issue_value=issue_value,
        issued_by=issued_by,
        pharmacist_id=pharmacist_id,
        is_cancelled=False
    )

    db.add(issue)
    await db.flush()

    return issue


async def get_pharmacy_issue(
    db: AsyncSession,
    issue_id: int,
    hospital_id: int,
    branch_id: int
) -> Optional[PharmacyIssue]:

    result = await db.execute(
        select(PharmacyIssue).where(
            PharmacyIssue.id == issue_id,
            PharmacyIssue.hospital_id == hospital_id,
            PharmacyIssue.branch_id == branch_id,
            PharmacyIssue.is_cancelled.is_(False)
        )
    )

    return result.scalar_one_or_none()


async def list_pharmacy_issues(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    item_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    patient_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[PharmacyIssue]:

    # Safety limit
    limit = min(limit, 200)

    query = select(PharmacyIssue).where(
        PharmacyIssue.hospital_id == hospital_id,
        PharmacyIssue.branch_id == branch_id,
        PharmacyIssue.is_cancelled.is_(False),
    )

    # Filters
    if item_type:
        query = query.where(PharmacyIssue.item_type == item_type)

    if reference_id:
        query = query.where(PharmacyIssue.reference_id == reference_id)

    if patient_type:
        query = query.where(PharmacyIssue.patient_type == patient_type)

    # Date filters
    if start_date:
        query = query.where(
            PharmacyIssue.issued_at >= datetime.combine(
                start_date,
                datetime.min.time()
            )
        )

    if end_date:
        query = query.where(
            PharmacyIssue.issued_at < datetime.combine(
                end_date + timedelta(days=1),
                datetime.min.time()
            )
        )

    # Sorting + Pagination
    query = (
        query.order_by(PharmacyIssue.issued_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)

    return result.scalars().all()


async def cancel_pharmacy_issue(
    db: AsyncSession,
    issue_id: int,
    hospital_id: int,
    branch_id: int
) -> bool:

    issue = await get_pharmacy_issue(
        db,
        issue_id,
        hospital_id,
        branch_id
    )

    if not issue:
        return False

    issue.is_cancelled = True

    await db.flush()

    return True