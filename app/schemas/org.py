from typing import Optional

from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    code: str
    location:str

class DepartmentCreate(BaseModel):
    name: str
    hospital_id: int
    branch_id: int


class DepartmentOut(BaseModel):
    id: int
    name: Optional[str]
    is_active: bool
    hospital_id: int
    branch_id: int
    hospital_name: str
    branch_name: str

    class Config:
        from_attributes = True