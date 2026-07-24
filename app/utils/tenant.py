# from fastapi import Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.core.security import get_current_user, get_db
#
# class Tenant:
#     def __init__(self, hospital_id: int, branch_id: int):
#         self.hospital_id = hospital_id
#         self.branch_id = branch_id
#
# def get_tenant(user = Depends(get_current_user), db: Session = Depends(get_db)) -> Tenant:
#     if not user.hospital_id or not user.current_branch_id:
#         raise HTTPException(400, detail="User has no active branch")
#     return Tenant(hospital_id=user.hospital_id, branch_id=user.current_branch_id)


# from fastapi import Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.core.security import get_current_user, get_db
#
# class Tenant:
#     def __init__(self, hospital_id: int, branch_id: int, user_id: int | None = None):
#         self.hospital_id = hospital_id
#         self.branch_id = branch_id
#         self.user_id = user_id
#
# def get_tenant(user = Depends(get_current_user), db: Session = Depends(get_db)) -> Tenant:
#     if not user.hospital_id or not user.current_branch_id:
#         raise HTTPException(400, detail="User has no active branch")
#     return Tenant(hospital_id=user.hospital_id, branch_id=user.current_branch_id, user_id=user.id)


# app/utils/tenant.py
from fastapi import Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import get_db, get_current_user
from app.models.org import Branch
from pydantic import BaseModel

class Tenant(BaseModel):
    hospital_id: int
    branch_id: int
    user_id: int

def get_tenant(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)) -> Tenant:
    # default from user
    branch_id = user.current_branch_id
    # optional override (header wins; you can also support ?branch_id=2)
    override = request.headers.get("X-Branch-Id") or request.query_params.get("branch_id")
    if override is not None:
        try:
            bid = int(override)
        except ValueError:
            raise HTTPException(400, "X-Branch-Id must be an integer")
        b = db.execute(
            select(Branch).where(Branch.id == bid, Branch.hospital_id == user.hospital_id, Branch.is_active == True)
        ).scalar_one_or_none()
        if not b:
            raise HTTPException(403, "Branch not found / not in your hospital")
        branch_id = bid

    return Tenant(hospital_id=user.hospital_id, branch_id=branch_id, user_id=user.id)
