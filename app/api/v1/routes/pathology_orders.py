from datetime import datetime
from collections import defaultdict
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import require_roles, get_current_user
from app.db.session import SessionLocal
from app.core.security import async_get_db
from app.models.people import Patient, Doctor
from app.models.pathology_tests  import Test, SampleType, Panel, PanelItem, Analyte, ReferenceRange
from app.models.pathology_orders  import LabOrder, LabOrderItem, Sample, Result, ResultValue, Validation, Report
from app.schemas.pathology_orders import OrderCreateIn, OrderOut, OrderItemOut, AccessionIn, ResultsBatchIn, ValidationIn, \
    ReportOut
from app.services.inapp_notify import notify_many, notify_user
import anyio
from app.services.reporting import generate_and_store_report

router = APIRouter(prefix="/orders", tags=["Orders"])

def _gen_series(prefix: str, n: int) -> str:
    y = datetime.utcnow().strftime("%Y%m")
    return f"{prefix}-{y}-{n:06d}"

# def _order_out(o: LabOrder) -> OrderOut:
#     items = [
#         OrderItemOut(id=i.id, test_id=i.test_id, panel_id=i.panel_id, sample_id=i.sample_id, status=i.status)
#         for i in o.items
#     ]
#     return OrderOut(
#         id=o.id, order_no=o.order_no, patient_id=o.patient_id, doctor_id=o.doctor_id,
#         priority=o.priority, source=o.source, status=o.status, items=items
#     )

def _order_out(o: LabOrder) -> OrderOut:
    items = [
        OrderItemOut(
            id=i.id,
            test_id=i.test_id,
            panel_id=i.panel_id,
            sample_id=i.sample_id,
            status=i.status,
        )
        for i in o.items
    ]

    # pick latest/current report
    latest_report = next((r for r in o.reports if r.is_current), None)
    reports = []
    if latest_report:
        reports.append(
            ReportOut(
                id=latest_report.id,
                version=latest_report.version,
                is_current=latest_report.is_current,
                pdf_url=latest_report.pdf_url,
            )
        )

    return OrderOut(
        id=o.id,
        order_no=o.order_no,
        patient_id=o.patient_id,
        doctor_id=o.doctor_id,
        priority=o.priority,
        source=o.source,
        status=o.status,
        items=items,
        reports=reports,  # only latest report
    )


def _get_age_days(dob):
    if not dob:
        return None
    return (datetime.utcnow().date() - dob).days

def _pick_range(db: Session, analyte_id: int, age_days: int | None, sex: str | None):
    q = db.query(ReferenceRange).filter(ReferenceRange.analyte_id == analyte_id)
    rs = q.all()
    if not rs:
        return None
    chosen = None
    for r in rs:
        if age_days is not None:
            if not (r.age_min_days <= age_days <= r.age_max_days):
                continue
        if sex and r.sex and r.sex != sex:
            continue
        chosen = r
        break
    if not chosen:
        chosen = rs[0]
    return chosen

def _flag_value(v: float | None, r: ReferenceRange | None) -> str:
    if v is None or r is None:
        return "N"
    if r.low is not None and v < r.low:
        return "L"
    if r.high is not None and v > r.high:
        return "H"
    return "N"

def _safe_eval_formula(formula: str, values_by_code: dict[str, float]) -> float | None:
    """
    Replace occurrences of {CODE} with values_by_code.get('CODE', 0) and eval
    with a safe environment.
    """
    if not formula:
        return None

    # transform "{A} + {B}/5" -> "(values.get('A',0)) + (values.get('B',0))/5"
    expr = formula
    for code in set([s.strip("{}") for s in formula.split() if s.startswith("{") and s.endswith("}")]):
        expr = expr.replace("{%s}" % code, f"(values.get('{code}', 0))")

    allowed = {"__builtins__": None, "abs": abs, "min": min, "max": max, "pow": pow, "round": round}
    try:
        return float(eval(expr, allowed, {"values": values_by_code}))
    except Exception:
        return None

async def _notify_doctor_result_entered(order_id: int):
    print("enter to the notification segment")
    db2 = SessionLocal()
    try:
        o2 = db2.get(LabOrder, order_id)
        if not o2:
            return
        print("o2",o2)
        doc_uid = o2.doctor.user_id if o2.doctor and o2.doctor.user_id else None
        print("doc",doc_uid)
        if not doc_uid:
            return
        await notify_user(
            db2, doc_uid,
            event="result_entered",
            title=f"Results entered for {o2.order_no}",
            body=f"Review and validate the report for {o2.patient.first_name} {o2.patient.last_name or ''}",
            order_id=o2.id,
            data={"order_no": o2.order_no}
        )
    except Exception as e:
        print("error occured",e)
    finally:
        db2.close()
from sqlalchemy import text

async def _notify_after_validation(order_id: int, validator_user_id: int):
    db2 = SessionLocal()
    try:
        o2 = db2.get(LabOrder, order_id)
        if not o2:
            return

        tech_user_ids = {it.result.entered_by for it in o2.items if it.result and it.result.entered_by}

        rows = db2.execute(text("""
            select users.id
            from users
            join user_roles ur on ur.user_id = users.id
            join roles r on r.id = ur.role_id
            where r.name = 'receptionist'
        """)).fetchall()
        reception_user_ids = {row[0] for row in rows}

        if tech_user_ids:
            await notify_many(
                db2, tech_user_ids,
                event="report_validated",
                title=f"Report validated for {o2.order_no}",
                body="Doctor approved the report; you can proceed.",
                order_id=o2.id,
                data={"order_no": o2.order_no}
            )
        if reception_user_ids:
            await notify_many(
                db2, reception_user_ids,
                event="report_validated",
                title=f"Report ready: {o2.order_no}",
                body="Invoice/dispatch if pending.",
                order_id=o2.id,
                data={"order_no": o2.order_no}
            )
    finally:
        db2.close()

from sqlalchemy.orm import selectinload, joinedload


def _current_doctor_id(db: Session, user) -> int | None:
    # Option B: you linked Doctor.user_id -> User.id
    doc = db.query(Doctor).filter(Doctor.user_id == user.id).one_or_none()
    return doc.id if doc else None

def _user_is_doctor_for_order(db: Session, user, order: LabOrder) -> bool:
    doc_id = _current_doctor_id(db, user)
    return bool(doc_id and order.doctor_id and order.doctor_id == doc_id)


@router.post("", response_model=OrderOut, dependencies=[Depends(require_roles(["super_admin", "admin", "receptionist"]))])
def create_order(payload: OrderCreateIn, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    if not db.get(Patient, payload.patient_id):
        raise HTTPException(400, "Invalid patient_id")
    if payload.doctor_id and not db.get(Doctor, payload.doctor_id):
        raise HTTPException(400, "Invalid doctor_id")

    # Expand panels to test_ids
    test_ids = set(payload.tests)
    if payload.panels:
        items = db.query(PanelItem).filter(PanelItem.panel_id.in_(payload.panels)).all()
        for it in items:
            test_ids.add(it.test_id)
    if not test_ids:
        raise HTTPException(400, "No tests provided")

    o = LabOrder(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        priority=payload.priority,
        source=payload.source,
        status="created",
        created_by=user.id,
    )
    db.add(o); db.flush()

    # Number after id is known
    o.order_no = _gen_series("ORD", o.id)

    for tid in sorted(test_ids):
        if not db.get(Test, tid):
            raise HTTPException(400, f"Invalid test_id: {tid}")
        db.add(LabOrderItem(order_id=o.id, test_id=tid, status="created"))

    db.commit(); db.refresh(o)
    return _order_out(o)


# Accession (Technician)
@router.post("/{order_id}/accession", response_model=OrderOut, dependencies=[Depends(require_roles(["technician", "admin", "super_admin"]))])
def accession(order_id: int, payload: AccessionIn, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")

    if o.status not in ("created", "sample_collected"):
        raise HTTPException(400, f"Order status {o.status} not eligible for accession")

    # group order items by sample_type
    by_type: dict[int, list[LabOrderItem]] = defaultdict(list)
    for it in o.items:
        t = db.get(Test, it.test_id)
        by_type[t.sample_type_id].append(it)

    # create samples and assign
    for st_id, items in by_type.items():
        s = Sample(sample_type_id=st_id, collected_by=user.id, remarks=payload.remarks)
        db.add(s); db.flush()
        s.accession_no = _gen_series("ACC", s.id)
        for it in items:
            it.sample_id = s.id
            it.status = "in_progress"

    o.status = "sample_collected"
    for it in o.items:
        if payload.sample_collected_at:
            it.sample_collected_at = payload.sample_collected_at
        if payload.sample_type_id:
            it.sample_type_id = payload.sample_type_id
    db.commit();db.refresh(o)
    return _order_out(o)


# Enter Results (Technician)
@router.post("/{order_id}/results", response_model=OrderOut, dependencies=[Depends(require_roles(["technician", "admin", "super_admin"]))])
def enter_results(order_id: int, payload: ResultsBatchIn, db: Session = Depends(async_get_db),user = Depends(get_current_user)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")

    # patient context for flagging
    patient = o.patient
    age_days = _get_age_days(patient.dob)
    sex = patient.sex

    for entry in payload.entries:
        it = db.get(LabOrderItem, entry.order_item_id)
        if not it or it.order_id != o.id:
            raise HTTPException(400, f"Invalid order_item_id {entry.order_item_id}")

        # create or reuse Result
        r = it.result
        if not r:
            r = Result(order_item_id=it.id, test_id=it.test_id, status="entered")
            db.add(r); db.flush()

        if not r.entered_by:
            r.entered_by = user.id

        if entry.test_interpretation is not None:
            r.test_interpretation = entry.test_interpretation
        if entry.test_note is not None:
            r.test_note = entry.test_note

        # load analytes for this test
        analytes = db.query(Analyte).filter(Analyte.test_id == it.test_id).all()
        by_id = {a.id: a for a in analytes}
        by_code = {a.code: a for a in analytes}

        # upsert measured values from request (supports interpretation/note)
        values_by_code: dict[str, float] = {}

        # existing values for this result (to avoid duplicates)
        existing = db.query(ResultValue).filter(ResultValue.result_id == r.id).all()
        existing_by_analyte = {rv.analyte_id: rv for rv in existing}

        for v in entry.values:
            a = by_id.get(v.analyte_id)
            if not a:
                raise HTTPException(400, f"Analyte {v.analyte_id} not in test {it.test_id}")

            num = v.value_num
            if num is not None:
                values_by_code[a.code] = num

            rr = _pick_range(db, a.id, age_days, sex)
            flag = _flag_value(num, rr)

            rv = existing_by_analyte.get(a.id)
            if not rv:
                rv = ResultValue(result_id=r.id, analyte_id=a.id)
                db.add(rv)

            rv.value_num = num
            rv.value_text = v.value_text
            rv.interpretation = v.interpretation  # NEW
            rv.note = v.note  # NEW
            rv.flag = flag

        for a in analytes:
            if a.is_calculated and a.formula:
                val = _safe_eval_formula(a.formula, values_by_code)
                if val is not None and not math.isnan(val) and not math.isinf(val):
                    values_by_code[a.code] = val
                    rr = _pick_range(db, a.id, age_days, sex)
                    flag = _flag_value(val, rr)

                    rv = existing_by_analyte.get(a.id)
                    if not rv:
                        rv = ResultValue(result_id=r.id, analyte_id=a.id)
                        db.add(rv)
                        existing_by_analyte[a.id] = rv  # keep dict in sync

                    rv.value_num = val
                    rv.value_text = None
                    rv.flag = flag

        it.status = "result_entered"

    # order-level status
    if all(i.status == "result_entered" for i in o.items):
        o.status = "result_entered"
    db.commit(); db.refresh(o)
    print("inserted to db successfully", o.id)
    anyio.from_thread.run(_notify_doctor_result_entered, o.id)
    return _order_out(o)


# Validate (Doctor)
@router.post("/{order_id}/validate", response_model=OrderOut, dependencies=[Depends(require_roles(["doctor", "super_admin", "admin"]))])
def validate_order(order_id: int, payload: ValidationIn, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status != "result_entered":
        raise HTTPException(400, f"Order must be in result_entered, found {o.status}")

    # mark each result validated
    for it in o.items:
        if not it.result:
            raise HTTPException(400, f"Missing result for item {it.id}")
        it.result.status = "validated"
        db.add(Validation(result_id=it.result.id, validated_by=user.id, comments=payload.comments or ""))

    o.status = "validated"
    db.commit(); db.refresh(o)
    # schedule notifications (techs + reception) with a fresh DB session
    anyio.from_thread.run(_notify_after_validation, o.id, user.id)

    # (optional) record who validated
    for it in o.items:
        if it.result:
            it.result.validated_by = user.id
    db.commit()
    return _order_out(o)

# Get order
@router.get("/{order_id}", response_model=OrderOut, dependencies=[Depends(require_roles(["super_admin", "admin", "receptionist", "technician", "doctor"]))])
def get_order(order_id: int, db: Session = Depends(async_get_db)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    return _order_out(o)



@router.post("/{order_id}/report", response_model=OrderOut, dependencies=[Depends(require_roles(["doctor", "super_admin", "admin"]))])
def create_report(order_id: int, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    o = db.get(LabOrder, order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    if o.status != "validated":
        raise HTTPException(400, f"Order must be validated, found {o.status}")

    rep = generate_and_store_report(db, order_id, user.id)
    # o.status is updated inside generate_and_store_report
    db.refresh(o)
    return _order_out(o)

@router.get("/{order_id}/results",dependencies=[Depends(require_roles(["doctor", "admin", "super_admin"]))],)
def get_order_results(order_id: int, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    from sqlalchemy.orm import selectinload

    o = (
        db.query(LabOrder)
        .options(
            selectinload(LabOrder.patient),

            # branch 1: items -> test
            selectinload(LabOrder.items).selectinload(LabOrderItem.test),

            # branch 2: items -> result -> values -> analyte -> unit
            selectinload(LabOrder.items)
            .selectinload(LabOrderItem.result)
            .selectinload(Result.values)
            .selectinload(ResultValue.analyte)
            .selectinload(Analyte.unit),
        )
        .filter(LabOrder.id == order_id)
        .one_or_none()
    )

    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    # If a doctor, enforce ownership (admins/super_admin can see all)
    # (If you already enforce this elsewhere, you can remove this block)
    try:
        # quick way to know if current user has doctor role; replace if you have a helper
        has_doctor_role = any(r.name == "doctor" for r in getattr(user, "roles", [])) if hasattr(user, "roles") else False
    except Exception:
        has_doctor_role = False

    if has_doctor_role and not _user_is_doctor_for_order(db, user, o):
        raise HTTPException(status_code=403, detail="Not your order")

    # Build review payload
    patient = o.patient
    patient_name = f"{patient.first_name} {patient.last_name or ''}".strip() if patient else ""
    out = {
        "order": {
            "id": o.id,
            "order_no": o.order_no,
            "status": o.status,
            "created_at": o.created_at.isoformat() if getattr(o, "created_at", None) else None,
        },
        "patient": {
            "id": o.patient_id,
            "name": patient_name,
            "sex": patient.sex if patient else None,
            "dob": patient.dob.isoformat() if (patient and patient.dob) else None,
            "code": patient.code if patient else None,
        },
        "items": [],
    }

    # for patient-based reference display
    age_days = _get_age_days(patient.dob) if patient else None
    sex = patient.sex if patient else None

    for it in o.items:
        res = it.result
        test = it.test
        rows = []
        if res:
            # include interpretation/note per test
            test_interp = res.test_interpretation
            test_note = res.test_note

            # each analyte row
            for rv in sorted(res.values, key=lambda x: x.analyte.code if x.analyte else 0):
                a = rv.analyte
                unit = a.unit.symbol if a and a.unit else None
                rr = _pick_range(db, a.id, age_days, sex) if a else None
                ref_txt = None
                if rr:
                    if rr.low is not None and rr.high is not None:
                        ref_txt = f"{rr.low} – {rr.high}"
                    elif rr.low is not None:
                        ref_txt = f"≥ {rr.low}"
                    elif rr.high is not None:
                        ref_txt = f"≤ {rr.high}"

                rows.append({
                    "analyte_id": a.id if a else None,
                    "analyte_code": a.code if a else None,
                    "analyte_name": a.name if a else None,
                    "value_num": rv.value_num,
                    "value_text": rv.value_text,
                    "interpretation": rv.interpretation,   # NEW
                    "note": rv.note,                       # NEW
                    "unit": unit,
                    "flag": rv.flag,
                    "reference": ref_txt,
                })
        out["items"].append({
            "order_item_id": it.id,
            "test_id": it.test_id,
            "test_code": test.code if test else None,
            "test_name": test.name if test else None,
            "status": it.status,
            "sample_collected_at": it.sample_collected_at.isoformat() if it.sample_collected_at else None,
            "sample_type_id": it.sample_type_id,
            "test_interpretation": getattr(res, "test_interpretation", None) if res else None,
            "test_note": getattr(res, "test_note", None) if res else None,
            "values": rows,
        })

    return out

@router.get("/review/my-pending",dependencies=[Depends(require_roles(["doctor", "admin", "super_admin"]))],)
def my_pending_orders(db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    q = (
        db.query(LabOrder)
          .options(selectinload(LabOrder.patient))
          .filter(LabOrder.status == "result_entered")
          .order_by(LabOrder.created_at.desc())
    )

    # If a doctor, show only orders assigned to this doctor
    try:
        has_doctor_role = any(r.name == "doctor" for r in getattr(user, "roles", [])) if hasattr(user, "roles") else False
    except Exception:
        has_doctor_role = False

    if has_doctor_role:
        my_doc_id = _current_doctor_id(db, user)
        if my_doc_id:
            q = q.filter(LabOrder.doctor_id == my_doc_id)

    items = []
    for o in q.limit(100).all():
        p = o.patient
        items.append({
            "order_id": o.id,
            "order_no": o.order_no,
            "patient_name": f"{p.first_name} {p.last_name or ''}".strip() if p else "",
            "patient_sex": p.sex if p else None,
            "created_at": o.created_at.isoformat() if getattr(o, "created_at", None) else None,
            "status": o.status,
        })
    return {"count": len(items), "items": items}
