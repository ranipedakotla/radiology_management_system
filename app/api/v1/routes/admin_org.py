from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.models.org import Branch
from app.schemas.org import BranchCreate
from app.utils.tenant import Tenant

from app.utils.tenant import get_tenant

router = APIRouter(prefix="/admin", tags=["Admin: branches"])


@router.post("/admin/branches")
def create_branch(payload: BranchCreate, tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    b = Branch(hospital_id=tenant.hospital_id, name=payload.name, code=payload.code, is_active=True)
    db.add(b); db.commit(); db.refresh(b)
    return b
