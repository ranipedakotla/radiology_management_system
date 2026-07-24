
from __future__ import annotations
from pydantic import BaseModel

class FloorIn(BaseModel):
    name: str
    description: str | None = None

class BedTypeIn(BaseModel):
    name: str

class BedGroupIn(BaseModel):
    name: str
    floor_name: str
    description: str | None = None

class BedIn(BaseModel):
    code: str
    bed_type_name: str
    bed_group_name: str

class BulkFloorsIn(BaseModel):
    floors: list[FloorIn]

class BulkBedTypesIn(BaseModel):
    bed_types: list[BedTypeIn]

class BulkBedGroupsIn(BaseModel):
    bed_groups: list[BedGroupIn]

class BulkBedsIn(BaseModel):
    beds: list[BedIn]

class BulkResult(BaseModel):
    created: int
    updated: int

class BedStatusItem(BaseModel):
    bed_code: str
    bed_type: str
    bed_group: str
    floor: str
    status: str  # "Allotted" | "Available"
