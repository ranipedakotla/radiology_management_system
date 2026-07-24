from datetime import datetime
from typing import Optional
from pydantic import BaseModel,ConfigDict


#from App.Accounting_utils.utils import LedgerType

# class LedgerCreate(BaseModel):
#     ledger_type: str
#     amount: float


# class LedgerResponse(LedgerCreate):
#     id: int

# class LedgerUpdate(BaseModel):
#         ledger_type: Optional[str] = None
#         amount: Optional[int] = None

# class LedgerOut(LedgerCreate):
#     id: int

# class LedgerIn(BaseModel):
#         id: int
#         created_at: datetime
# #
# # class Config:
# #         from_attributes = True

class LedgerBase(BaseModel):
    ledger_type: str
    amount: float

class LedgerCreate(LedgerBase):
    hospital_id: int
    branch_id: int  

class LedgerUpdate(BaseModel):
    ledger_type: Optional[str] = None
    amount: Optional[float] = None
    hospital_id: Optional[int] = None
    branch_id: Optional[int] = None


class LedgerOut(LedgerBase):
    id: int
    hospital_id: int
    branch_id: int

    model_config = ConfigDict(from_attributes=True)          

class LedgerResponse(LedgerOut):
    created_at: datetime   
