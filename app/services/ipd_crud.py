import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
import uuid
from app.models.ipd_models import MedicineReturn, WardMedicineIssue
from app.models.entry_models import PharmacyIssue
from app.schemas.ipd_schemasp import WardIssueOut


async def create_ward_issue(db: AsyncSession, ward_issue: WardMedicineIssue):
    db.add(ward_issue)
    await db.commit()
    await db.refresh(ward_issue)
    return ward_issue


async def create_medicine_return(db: AsyncSession, medicine_return: MedicineReturn):
    db.add(medicine_return)
    await db.commit()
    await db.refresh(medicine_return)
    return medicine_return


async def get_issue_by_ref(
    db: AsyncSession,
    issue_ref: str,
    hospital_id: int,
    branch_id: int
):
    issue_uuid = uuid.UUID(issue_ref)

    result = await db.execute(
        select(WardMedicineIssue).where(
            WardMedicineIssue.issue_ref == issue_uuid.bytes,
            WardMedicineIssue.hospital_id == hospital_id,
            WardMedicineIssue.branch_id == branch_id,
        )
    )
    return result.scalars().first()

async def get_issues_by_patient_uhid(
    db: AsyncSession,
    patient_uhid: str,
    hospital_id: int,
    branch_id: int,
):
    result = await db.execute(
        select(WardMedicineIssue).where(
            WardMedicineIssue.patient_uhid == patient_uhid,
            WardMedicineIssue.hospital_id == hospital_id,
            WardMedicineIssue.branch_id == branch_id,
        )
    )

    issues = result.scalars().all()

    return [
        WardIssueOut(
            issue_ref=str(uuid.UUID(bytes=issue.issue_ref)),
            patient_uhid=issue.patient_uhid,
            ward_id=issue.ward_id,
            hospital_id=issue.hospital_id,
            branch_id=issue.branch_id,
            total_amount=issue.total_amount,
            issued_at=issue.issued_at,
            status=issue.status,
            payment_mode=issue.payment_mode,
            noc_number=issue.noc_number,
        )
        for issue in issues
    ]
