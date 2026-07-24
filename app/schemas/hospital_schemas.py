# from pydantic import BaseModel
# from typing import List, Optional
#
# class HospitalBase(BaseModel):
#     name: str
#
# class HospitalCreate(HospitalBase):
#     pass
#
# class Hospital(HospitalBase):
#     id: int
#     is_active: bool
#     branches: List['HospitalBranch'] = []
#
#     class Config:
#         from_attributes = True
#
# class HospitalBranchBase(BaseModel):
#     name: str
#     location: Optional[str] = None
#     contact_number: Optional[str] = None
#
# class HospitalBranchCreate(HospitalBranchBase):
#     pass  # No hospital_id needed - auto-links to singleton hospital
#
# class HospitalBranch(HospitalBranchBase):
#     id: int
#     hospital_id: int
#
#     class Config:
#         from_attributes = True


from pydantic import BaseModel
from typing import List, Optional


class HospitalBase(BaseModel):
    name: str

class HospitalAmbulanceCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    address: str
    city: str
    latitude: float
    longitude: float


class HospitalCreate(HospitalBase):
    pass


class HospitalAmbulanceResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: str
    city: str
    latitude: float
    longitude: float
    emergency_available: bool
    status: str

    class Config:
        from_attributes = True

class Hospital(HospitalBase):
    id: int
    is_active: bool
    branches: List['HospitalBranch'] = []

    class Config:
        from_attributes = True


class HospitalBranchBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = None
    contact_number: Optional[str] = None


class HospitalBranchCreate(HospitalBranchBase):
    pass


class HospitalBranch(HospitalBranchBase):
    id: int
    hospital_id: int

    class Config:
        from_attributes = True

