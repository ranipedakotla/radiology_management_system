from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.core.security import async_get_db
from app.models.pathology_tests import Unit, SampleType, Test, Analyte, ReferenceRange, Panel, PanelItem
from app.schemas.catalog import (
    UnitIn, UnitOut,
    SampleTypeIn, SampleTypeOut,
    TestCreateIn, TestPatchIn, TestOut, AnalyteOut, ReferenceRangeOut,
    PanelCreateIn, PanelItemAddIn, PanelOut, PanelOutItem
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])

WriteDep = Depends(require_roles(["super_admin", "admin"]))
ReadDep  = Depends(require_roles(["super_admin", "admin", "receptionist", "technician", "doctor"]))


# ---------- helpers ----------
def _rr_out(r: ReferenceRange) -> ReferenceRangeOut:
    return ReferenceRangeOut(
        id=r.id, sex=r.sex, age_min_days=r.age_min_days, age_max_days=r.age_max_days,
        low=r.low, high=r.high, note=r.note
    )

def _an_out(a: Analyte) -> AnalyteOut:
    return AnalyteOut(
        id=a.id, code=a.code, name=a.name, unit_id=a.unit_id, is_calculated=a.is_calculated, formula=a.formula,
        ranges=[_rr_out(r) for r in a.ranges]
    )

def _test_out(t: Test) -> TestOut:
    return TestOut(
        id=t.id, code=t.code, name=t.name, method=t.method, sample_type_id=t.sample_type_id,
        category=t.category, tat_hours=t.tat_hours, is_active=t.is_active,
        analytes=[_an_out(a) for a in t.analytes]
    )

def _panel_out(p: Panel) -> PanelOut:
    items = [
        PanelOutItem(id=i.id, test_id=i.test_id, test_code=i.test.code, test_name=i.test.name)
        for i in p.items
    ]
    return PanelOut(id=p.id, code=p.code, name=p.name, is_active=p.is_active, items=items)


# ---------- Units ----------
@router.post("/units", response_model=UnitOut, dependencies=[WriteDep])
def create_unit(payload: UnitIn, db: Session = Depends(async_get_db)):
    if db.query(Unit).filter(Unit.symbol == payload.symbol).one_or_none():
        raise HTTPException(400, "Unit symbol already exists")
    u = Unit(symbol=payload.symbol, name=payload.name)
    db.add(u); db.commit(); db.refresh(u)
    return UnitOut(id=u.id, symbol=u.symbol, name=u.name)

@router.get("/units", response_model=List[UnitOut], dependencies=[ReadDep])
def list_units(db: Session = Depends(async_get_db)):
    xs = db.query(Unit).order_by(Unit.symbol.asc()).all()
    return [UnitOut(id=x.id, symbol=x.symbol, name=x.name) for x in xs]


# ---------- Sample Types ----------
@router.post("/sample-types", response_model=SampleTypeOut, dependencies=[WriteDep])
def create_sample_type(payload: SampleTypeIn, db: Session = Depends(async_get_db)):
    if db.query(SampleType).filter(SampleType.name == payload.name).one_or_none():
        raise HTTPException(400, "Sample type already exists")
    s = SampleType(name=payload.name)
    db.add(s); db.commit(); db.refresh(s)
    return SampleTypeOut(id=s.id, name=s.name)

@router.get("/sample-types", response_model=List[SampleTypeOut], dependencies=[ReadDep])
def list_sample_types(db: Session = Depends(async_get_db)):
    xs = db.query(SampleType).order_by(SampleType.name.asc()).all()
    return [SampleTypeOut(id=x.id, name=x.name) for x in xs]


# ---------- Tests (with analytes + ranges) ----------
@router.post("/tests", response_model=TestOut, dependencies=[WriteDep])
def create_test(payload: TestCreateIn, db: Session = Depends(async_get_db)):
    if db.query(Test).filter(Test.code == payload.code).one_or_none():
        raise HTTPException(400, "Test code already exists")

    # Validate sample_type
    if not db.get(SampleType, payload.sample_type_id):
        raise HTTPException(400, "Invalid sample_type_id")

    t = Test(
        code=payload.code, name=payload.name, method=payload.method,
        sample_type_id=payload.sample_type_id, category=payload.category,
        tat_hours=payload.tat_hours, is_active=payload.is_active
    )
    db.add(t); db.flush()

    for an in payload.analytes:
        if an.unit_id and not db.get(Unit, an.unit_id):
            raise HTTPException(400, f"Invalid unit_id for analyte {an.code}")
        a = Analyte(
            test_id=t.id, code=an.code, name=an.name, unit_id=an.unit_id,
            is_calculated=an.is_calculated, formula=an.formula
        )
        db.add(a); db.flush()
        for rr in an.ranges:
            db.add(ReferenceRange(
                analyte_id=a.id,
                sex=rr.sex,
                age_min_days=rr.age_min_days,
                age_max_days=rr.age_max_days,
                low=rr.low, high=rr.high, note=rr.note
            ))

    db.commit(); db.refresh(t)
    return _test_out(t)

@router.get("/tests", response_model=List[TestOut], dependencies=[ReadDep])
def list_tests(
    search: Optional[str] = Query(default=None),
    active: Optional[bool] = None,
    db: Session = Depends(async_get_db),
):
    q = db.query(Test)
    if search:
        like = f"%{search}%"
        q = q.filter((Test.code.ilike(like)) | (Test.name.ilike(like)))
    if active is not None:
        q = q.filter(Test.is_active == active)
    xs = q.order_by(Test.name.asc()).all()
    return [_test_out(t) for t in xs]

@router.get("/tests/{test_id}", response_model=TestOut, dependencies=[ReadDep])
def get_test(test_id: int, db: Session = Depends(async_get_db)):
    t = db.get(Test, test_id)
    if not t:
        raise HTTPException(404, "Test not found")
    return _test_out(t)

@router.patch("/tests/{test_id}", response_model=TestOut, dependencies=[WriteDep])
def patch_test(test_id: int, payload: TestPatchIn, db: Session = Depends(async_get_db)):
    t = db.get(Test, test_id)
    if not t:
        raise HTTPException(404, "Test not found")

    data = payload.model_dump(exclude_unset=True)
    if "sample_type_id" in data and not db.get(SampleType, data["sample_type_id"]):
        raise HTTPException(400, "Invalid sample_type_id")

    for k, v in data.items():
        setattr(t, k, v)

    db.commit(); db.refresh(t)
    return _test_out(t)


# ---------- Panels ----------
@router.post("/panels", response_model=PanelOut, dependencies=[WriteDep])
def create_panel(payload: PanelCreateIn, db: Session = Depends(async_get_db)):
    if db.query(Panel).filter(Panel.code == payload.code).one_or_none():
        raise HTTPException(400, "Panel code already exists")
    p = Panel(code=payload.code, name=payload.name, is_active=payload.is_active)
    db.add(p); db.flush()

    for tid in payload.test_ids:
        t = db.get(Test, tid)
        if not t:
            raise HTTPException(400, f"Invalid test_id {tid}")
        db.add(PanelItem(panel_id=p.id, test_id=t.id))

    db.commit(); db.refresh(p)
    return _panel_out(p)

@router.post("/panels/{panel_id}/items", response_model=PanelOut, dependencies=[WriteDep])
def add_panel_item(panel_id: int, payload: PanelItemAddIn, db: Session = Depends(async_get_db)):
    p = db.get(Panel, panel_id)
    if not p:
        raise HTTPException(404, "Panel not found")
    t = db.get(Test, payload.test_id)
    if not t:
        raise HTTPException(400, "Invalid test_id")
    exists = (
        db.query(PanelItem)
          .filter(PanelItem.panel_id == panel_id, PanelItem.test_id == t.id)
          .one_or_none()
    )
    if not exists:
        db.add(PanelItem(panel_id=panel_id, test_id=t.id))
        db.commit()
    db.refresh(p)
    return _panel_out(p)

@router.get("/panels", response_model=List[PanelOut], dependencies=[ReadDep])
def list_panels(
    search: Optional[str] = Query(default=None),
    active: Optional[bool] = None,
    db: Session = Depends(async_get_db),
):
    q = db.query(Panel)
    if search:
        like = f"%{search}%"
        q = q.filter((Panel.code.ilike(like)) | (Panel.name.ilike(like)))
    if active is not None:
        q = q.filter(Panel.is_active == active)
    xs = q.order_by(Panel.name.asc()).all()
    return [_panel_out(p) for p in xs]
