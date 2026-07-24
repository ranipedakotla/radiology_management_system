
from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# Optional (prepare for branch switching later)
class SwitchBranchIn(BaseModel):
    branch_id: int


