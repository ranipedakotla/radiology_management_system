from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Sex = Literal["M", "F", "O"]


# --- Units & Sample Types ---
class UnitIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    name: str = Field(min_length=1, max_length=64)

class UnitOut(BaseModel):
    id: int
    symbol: str
    name: str

class SampleTypeIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)

class SampleTypeOut(BaseModel):
    id: int
    name: str


# --- Reference Ranges ---
class ReferenceRangeIn(BaseModel):
    sex: Optional[Sex] = None
    age_min_days: int = 0
    age_max_days: int = 365000
    low: Optional[float] = None
    high: Optional[float] = None
    note: Optional[str] = None

class ReferenceRangeOut(BaseModel):
    id: int
    sex: Optional[Sex]
    age_min_days: int
    age_max_days: int
    low: Optional[float]
    high: Optional[float]
    note: Optional[str]


# --- Analytes ---
class AnalyteIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    unit_id: Optional[int] = None
    is_calculated: bool = False
    formula: Optional[str] = None
    ranges: List[ReferenceRangeIn] = Field(default_factory=list)

class AnalyteOut(BaseModel):
    id: int
    code: str
    name: str
    unit_id: Optional[int]
    is_calculated: bool
    formula: Optional[str]
    ranges: List[ReferenceRangeOut]


# --- Tests ---
class TestCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    method: Optional[str] = Field(default=None, max_length=64)
    sample_type_id: int
    category: Optional[str] = Field(default=None, max_length=64)
    tat_hours: int = 24
    is_active: bool = True
    analytes: List[AnalyteIn] = Field(default_factory=list)

class TestPatchIn(BaseModel):
    name: Optional[str] = None
    method: Optional[str] = None
    sample_type_id: Optional[int] = None
    category: Optional[str] = None
    tat_hours: Optional[int] = None
    is_active: Optional[bool] = None

class TestOut(BaseModel):
    id: int
    code: str
    name: str
    method: Optional[str]
    sample_type_id: int
    category: Optional[str]
    tat_hours: int
    is_active: bool
    analytes: List[AnalyteOut]


# --- Panels ---
class PanelCreateIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    is_active: bool = True
    test_ids: List[int] = Field(default_factory=list)

class PanelItemAddIn(BaseModel):
    test_id: int

class PanelOutItem(BaseModel):
    id: int
    test_id: int
    test_code: str
    test_name: str

class PanelOut(BaseModel):
    id: int
    code: str
    name: str
    is_active: bool
    items: List[PanelOutItem]
