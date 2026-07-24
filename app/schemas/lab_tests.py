from pydantic import BaseModel
from typing import Optional


# ==========================================
# Create Lab Test
# ==========================================
class LabTestCreate(BaseModel):

    test_type: str
    test_sub_type: str
    cost: float
    body_part: str

    precautions: Optional[str] = None

    id_proof_required: bool = False


# ==========================================
# Update Lab Test
# ==========================================
class LabTestUpdate(BaseModel):

    test_type: str
    test_sub_type: str
    cost: float
    body_part: str

    precautions: Optional[str] = None

    id_proof_required: bool = False

    is_active: bool


# ==========================================
# Lab Test Response
# ==========================================
class LabTestResponse(BaseModel):

    id: int

    test_type: str
    test_sub_type: str

    cost: float

    body_part: str

    precautions: Optional[str]

    id_proof_required: bool

    is_active: bool

    class Config:
        from_attributes = True


# ==========================================
# Lab Test Availability Response
# ==========================================
class LabTestAvailabilityResponse(BaseModel):

    id: int

    test_type: str

    test_sub_type: str

    is_available: bool

    message: str