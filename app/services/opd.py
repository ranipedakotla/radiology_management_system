# app/services/opd.py
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.models.opd import OPDVisit, OPDVisitDiagnosis, Prescription, PrescriptionItem, OpdVisitLabTest
from app.models.people import Patient, Doctor, Staff
from app.models.appointments import Appointment
from app.utils.tenant import Tenant
from sqlalchemy.orm import Session
from app.services._tenant_utils import _set_tenant_fields, _filter_by_tenant, _get_by_id_scoped


class OPDService:

    def __init__(self, db: Session, tenant):
        self.db = db
        self.tenant = tenant

    def create_visit(self, payload):

        with SessionLocal() as db:

            # validate appointment
            appointment = db.execute(
                select(Appointment).where(
                    Appointment.id == payload.appointment_id
                )
            ).scalars().first()

            if not appointment:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid appointment_id"
                )

            if payload.vitals:

                if (payload.vitals.blood_sugar_bf is not None
                        and not (40 <= payload.vitals.blood_sugar_bf <= 600)):
                    raise HTTPException(
                        status_code=400,
                        detail="Blood sugar (BF) must be between 40 and 600 mg/dL"
                    )

                if (
                        payload.vitals.blood_sugar_af is not None
                        and not (40 <= payload.vitals.blood_sugar_af <= 600)
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Blood sugar (AF) must be between 40 and 600 mg/dL"
                    )

            seen_icd_codes = set()

            for d in (payload.diagnoses or []):
                code = (d.icd_code or "").strip().upper()

                if code in seen_icd_codes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate diagnosis code: {d.icd_code}"
                    )

                seen_icd_codes.add(code)

            # duplicate medicine validation
            seen_drugs = set()

            for item in (payload.prescription_items or []):
                drug = (item.drug_name or "").strip().lower()

                if drug in seen_drugs:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate medicine: {item.drug_name}"
                    )

                seen_drugs.add(drug)

            # duplicate lab test validation
            seen_tests = set()

            for lt in (payload.lab_tests or []):
                code = (lt.test_code or "").strip().upper()

                if code in seen_tests:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate lab test code: {lt.test_code}"
                    )

                seen_tests.add(code)

            visit = OPDVisit(
                visit_id=f"OPD{datetime.utcnow().strftime('%y%m%d%H%M%S')}",

                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                appointment_id=payload.appointment_id,

                visit_date=payload.visit_date or datetime.utcnow(),

                chief_complaint=payload.chief_complaint,
                symptoms=payload.symptoms,
                notes=payload.notes,

                height_cm=payload.vitals.height_cm if payload.vitals else None,
                weight_kg=payload.vitals.weight_kg if payload.vitals else None,
                temp_c=payload.vitals.temp_c if payload.vitals else None,
                bp_systolic=payload.vitals.bp_systolic if payload.vitals else None,
                bp_diastolic=payload.vitals.bp_diastolic if payload.vitals else None,
                blood_sugar_bf=payload.vitals.blood_sugar_bf if payload.vitals else None,
                blood_sugar_af=payload.vitals.blood_sugar_af if payload.vitals else None,
                pulse=payload.vitals.pulse if payload.vitals else None,
                resp_rate=payload.vitals.resp_rate if payload.vitals else None,
                spo2=payload.vitals.spo2 if payload.vitals else None,

                hospital_id=self.tenant.hospital_id,
                branch_id=self.tenant.branch_id,
            )

            db.add(visit)
            db.flush()

            # diagnoses
            for d in payload.diagnoses:
                diag = OPDVisitDiagnosis(
                    visit_id=visit.id,
                    icd_code=d.icd_code,
                    description=d.description,
                    is_primary=d.is_primary,

                    # hospital_id=self.tenant.hospital_id,
                    # branch_id=self.tenant.branch_id,
                )

                db.add(diag)

            # prescription
            if payload.prescription_items:

                prescription = Prescription(
                    visit_id=visit.id,
                    # hospital_id=self.tenant.hospital_id,
                    # branch_id=self.tenant.branch_id,
                )

                db.add(prescription)
                db.flush()

                for item in payload.prescription_items:
                    db.add(
                        PrescriptionItem(
                            prescription_id=prescription.id,

                            drug_name=item.drug_name,
                            dose=item.dose,
                            frequency=item.frequency,
                            duration=item.duration,
                            route=item.route,
                            instructions=item.instructions,
                            quantity=item.quantity,
                            unit=item.unit,

                            # hospital_id=self.tenant.hospital_id,
                            # branch_id=self.tenant.branch_id,
                        )
                    )

            # lab tests
            for lt in payload.lab_tests:
                db.add(
                    OpdVisitLabTest(
                        visit_id=visit.id,

                        test_name=lt.test_name,
                        test_code=lt.test_code,
                        priority=lt.priority,
                        notes=lt.notes,
                        status="Ordered",

                        # hospital_id=self.tenant.hospital_id,
                        # branch_id=self.tenant.branch_id,
                    )
                )

            db.commit()
            db.refresh(visit)

            return self.get_visit(visit.id, visit.appointment_id)

    def get_visit(self, visit_id: int, appointment_id: int) -> dict:

        db = self.db

        hdr = (
            select(
                OPDVisit,

                Patient.first_name.label("p_fn"),
                Patient.last_name.label("p_ln"),
                Patient.age.label("p_age"),
                Patient.gender.label("p_gender"),
                Patient.phone_number.label("p_phone"),

                Staff.first_name.label("d_fn"),
                Staff.last_name.label("d_ln"),

                Doctor.department.label("department")
            )
            .join(Patient, Patient.id == OPDVisit.patient_id)
            .join(Doctor, Doctor.id == OPDVisit.doctor_id)
            .join(Staff, Staff.id == Doctor.staff_id)
            .where(OPDVisit.id == visit_id)
        )
        if appointment_id is not None:
            hdr = hdr.where(OPDVisit.appointment_id == appointment_id)

        hdr = _filter_by_tenant(
            hdr,
            OPDVisit,
            self.tenant
        )

        row = db.execute(hdr).first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Visit not found"
            )

        v: OPDVisit = row[0]

        p_name = f"{row.p_fn} {row.p_ln}".strip()
        d_name = f"{row.d_fn} {row.d_ln}".strip()

        diags = db.execute(
            _filter_by_tenant(
                select(OPDVisitDiagnosis).where(
                    OPDVisitDiagnosis.visit_id == visit_id
                ),
                OPDVisitDiagnosis,
                self.tenant
            )
        ).scalars().all()

        diagnoses = [
            {
                "icd_code": d.icd_code,
                "description": d.description,
                "is_primary": d.is_primary
            }
            for d in diags
        ]

        pr = db.execute(
            _filter_by_tenant(
                select(Prescription)
                .where(Prescription.visit_id == visit_id)
                .order_by(Prescription.id.asc()),
                Prescription,
                self.tenant
            )
        ).scalars().first()

        items = []

        if pr:
            rows = db.execute(
                _filter_by_tenant(
                    select(PrescriptionItem).where(
                        PrescriptionItem.prescription_id == pr.id
                    ),
                    PrescriptionItem,
                    self.tenant
                )
            ).scalars().all()
            items = [
                {
                    "drug_name": it.drug_name,
                    "dose": it.dose,
                    "frequency": it.frequency,
                    "duration": it.duration,
                    "route": it.route,
                    "instructions": it.instructions,
                    "quantity": it.quantity,
                    "unit": it.unit,
                }
                for it in rows
            ]

        lab_rows = db.execute(
            _filter_by_tenant(
                select(OpdVisitLabTest)
                .where(OpdVisitLabTest.visit_id == visit_id)
                .order_by(OpdVisitLabTest.id.asc()),
                OpdVisitLabTest,
                self.tenant
            )
        ).scalars().all()
        lab_tests = [
            {
                "id": lt.id,
                "test_name": lt.test_name,
                "test_code": lt.test_code,
                "priority": lt.priority,
                "notes": lt.notes,
                "status": lt.status,
            }
            for lt in lab_rows
        ]
        vitals = {
            "height_cm": v.height_cm,
            "weight_kg": v.weight_kg,
            "temp_c": v.temp_c,
            "bp_systolic": v.bp_systolic,
            "bp_diastolic": v.bp_diastolic,
            "blood_sugar_bf": v.blood_sugar_bf,
            "blood_sugar_af": v.blood_sugar_af,
            "pulse": v.pulse,
            "resp_rate": v.resp_rate,
            "spo2": v.spo2,
        }
        return {
            "id": v.id,
            "visit_id": v.visit_id,
            "patient_name": p_name,
            "appointment_id": v.appointment_id,
            "department": row.department,
            "age": row.p_age,
            "gender": row.p_gender,
            "patient_id": v.patient_id,
            "doctor_id": v.doctor_id,
            "phone_number": row.p_phone,
            "doctor_name": d_name,
            "visit_date": v.visit_date,
            "chief_complaint": v.chief_complaint,
            "symptoms": v.symptoms,
            "notes": v.notes,
            "blood_sugar_bf": v.blood_sugar_bf,
            "blood_sugar_af": v.blood_sugar_af,
            "vitals": vitals,
            "diagnoses": diagnoses,
            "prescription": items,
            "lab_tests": lab_tests,
        }

    def list_visits(self, patient_id: int | None, doctor_id: int | None, date_from: datetime | None,
                    date_to: datetime | None,
                    page: int, page_size: int, appointment_id: int):
        with SessionLocal() as db:
            base = (
                select(
                    OPDVisit,
                    Patient.first_name.label("p_fn"),
                    Patient.last_name.label("p_ln"),
                    Staff.first_name.label("d_fn"),
                    Staff.last_name.label("d_ln"),
                    Doctor.department.label("department")

                )
                .join(Patient, Patient.id == OPDVisit.patient_id)
                .join(Doctor, Doctor.id == OPDVisit.doctor_id)
                .join(Staff, Staff.id == Doctor.staff_id)
            )
            base = _filter_by_tenant(base, OPDVisit, self.tenant)
            base = _filter_by_tenant(base, Patient, self.tenant)
            base = _filter_by_tenant(base, Doctor, self.tenant)
            if patient_id:
                base = base.where(OPDVisit.patient_id == patient_id)

            if doctor_id:
                base = base.where(OPDVisit.doctor_id == doctor_id)

            if appointment_id:
                base = base.where(OPDVisit.appointment_id == appointment_id)

            if date_from and date_to:
                base = base.where(
                    OPDVisit.visit_date.between(date_from, date_to)
                )

            elif date_from:
                base = base.where(
                    OPDVisit.visit_date >= date_from
                )

            elif date_to:
                base = base.where(
                    OPDVisit.visit_date <= date_to
                )
            total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
            rows = db.execute(
                base.order_by(OPDVisit.visit_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()

            items = []
            for row in rows:
                v: OPDVisit = row[0]
                p_name = f"{row.p_fn} {row.p_ln}".strip()
                d_name = f"{row.d_fn} {row.d_ln}".strip()
                items.append(
                    {
                        "id": v.id,
                        "visit_id": v.visit_id,
                        "patient_name": p_name,
                        "department": row.department,
                        "doctor_name": d_name,
                        "visit_date": v.visit_date,
                        "patient_id": v.patient_id,
                        "doctor_id": v.doctor_id,
                        "appointment_id": v.appointment_id,
                        # "ward_name": v.ward_name,
                        "chief_complaint": v.chief_complaint,
                    }
                )
            return items, total

    def update_visit(self, visit_id: int, payload) -> dict:
        with SessionLocal() as db:

            visit = db.execute(
                _filter_by_tenant(
                    select(OPDVisit).where(OPDVisit.id == visit_id),
                    OPDVisit,
                    self.tenant
                )
            ).scalars().first()

            if not visit:
                raise HTTPException(status_code=404, detail="Visit not found")

            # validate appointment
            appointment = db.execute(
                select(Appointment).where(
                    Appointment.id == payload.appointment_id
                )
            ).scalars().first()

            if not appointment:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid appointment_id"
                )

            # update visit fields
            visit.doctor_id = payload.doctor_id
            visit.appointment_id = payload.appointment_id
            visit.visit_date = payload.visit_date or visit.visit_date
            visit.chief_complaint = payload.chief_complaint
            visit.symptoms = payload.symptoms
            visit.notes = payload.notes

            # vitals
            if payload.vitals:
                visit.height_cm = payload.vitals.height_cm
                visit.weight_kg = payload.vitals.weight_kg
                visit.temp_c = payload.vitals.temp_c
                visit.bp_systolic = payload.vitals.bp_systolic
                visit.bp_diastolic = payload.vitals.bp_diastolic
                visit.blood_sugar_bf = payload.vitals.blood_sugar_bf
                visit.blood_sugar_af = payload.vitals.blood_sugar_af
                visit.pulse = payload.vitals.pulse
                visit.resp_rate = payload.vitals.resp_rate
                visit.spo2 = payload.vitals.spo2

            # delete old diagnoses
            old_diags = db.execute(
                select(OPDVisitDiagnosis).where(
                    OPDVisitDiagnosis.visit_id == visit_id
                )
            ).scalars().all()

            for d in old_diags:
                db.delete(d)

            # duplicate diagnosis validation
            seen_icd = set()
            for d in payload.diagnoses:
                if d.icd_code in seen_icd:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate diagnosis code: {d.icd_code}"
                    )
                seen_icd.add(d.icd_code)

            # duplicate lab test validation
            seen_tests = set()
            for lt in payload.lab_tests:
                if lt.test_code in seen_tests:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate lab test code: {lt.test_code}"
                    )
                seen_tests.add(lt.test_code)

            # duplicate medicine validation
            seen_drugs = set()
            for item in payload.prescription_items or []:
                drug = item.drug_name.strip().lower()

                if drug in seen_drugs:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate medicine: {item.drug_name}"
                    )

                seen_drugs.add(drug)

            # add new diagnoses
            for d in payload.diagnoses:
                db.add(OPDVisitDiagnosis(
                    visit_id=visit.id,
                    icd_code=d.icd_code,
                    description=d.description,
                    is_primary=d.is_primary,
                    # hospital_id=self.tenant.hospital_id,
                    # branch_id=self.tenant.branch_id,
                ))

            # prescription
            old_prescriptions = db.execute(
                select(Prescription).where(
                    Prescription.visit_id == visit_id
                )
            ).scalars().all()

            for pr in old_prescriptions:

                old_items = db.execute(
                    select(PrescriptionItem).where(
                        PrescriptionItem.prescription_id == pr.id
                    )
                ).scalars().all()

                for item in old_items:
                    db.delete(item)

                db.delete(pr)

            # create new prescription
            if payload.prescription_items:

                new_pr = Prescription(
                    visit_id=visit.id,
                    # hospital_id=self.tenant.hospital_id,
                    # branch_id=self.tenant.branch_id,
                )

                db.add(new_pr)
                db.flush()

                for item in payload.prescription_items:
                    db.add(PrescriptionItem(
                        prescription_id=new_pr.id,
                        drug_name=item.drug_name,
                        dose=item.dose,
                        frequency=item.frequency,
                        duration=item.duration,
                        route=item.route,
                        instructions=item.instructions,
                        quantity=item.quantity,
                        unit=item.unit,
                        # hospital_id=self.tenant.hospital_id,
                        # branch_id=self.tenant.branch_id,
                    ))

            # lab tests
            old_tests = db.execute(
                select(OpdVisitLabTest).where(
                    OpdVisitLabTest.visit_id == visit_id
                )
            ).scalars().all()

            for t in old_tests:
                db.delete(t)

            for lt in payload.lab_tests:
                db.add(OpdVisitLabTest(
                    visit_id=visit.id,
                    test_name=lt.test_name,
                    test_code=lt.test_code,
                    priority=lt.priority,
                    notes=lt.notes,
                    status="Ordered",
                    # hospital_id=self.tenant.hospital_id,
                    # branch_id=self.tenant.branch_id,
                ))

            db.commit()

            return self.get_visit(
                visit.id,
                visit.appointment_id
            )

    def _get_visit_scoped(self, db, visit_id):
        stmt = select(OPDVisit).where(OPDVisit.id == visit_id)
        stmt = _filter_by_tenant(stmt, OPDVisit, self.tenant)
        return db.execute(stmt).scalar_one_or_none()

    def add_vitals(
            self, visit_id,
            height_cm, weight_kg, temp_c,
            bp_systolic, bp_diastolic, blood_sugar_bf, blood_sugar_af,
            pulse, resp_rate, spo2):
        with SessionLocal() as db:
            visit = self._get_visit_scoped(db, visit_id)

            if not visit:
                raise HTTPException(404, "Visit not found")

            # overwrite (same as create)
            visit.height_cm = height_cm
            visit.weight_kg = weight_kg
            visit.temp_c = temp_c
            visit.bp_systolic = bp_systolic
            visit.bp_diastolic = bp_diastolic
            visit.pulse = pulse
            visit.resp_rate = resp_rate
            visit.spo2 = spo2
            visit.blood_sugar_bf = blood_sugar_bf
            visit.blood_sugar_af = blood_sugar_af
            db.commit()
            db.refresh(visit)
            return {"message": "Vitals added", "visit_id": visit.id}

    def update_vitals(
            self, visit_id,
            height_cm, weight_kg, temp_c,
            bp_systolic, bp_diastolic,
            blood_sugar_bf, blood_sugar_af,
            pulse, resp_rate, spo2
    ):
        with SessionLocal() as db:
            visit = self._get_visit_scoped(db, visit_id)

            if not visit:
                raise HTTPException(404, "Visit not found")

            if height_cm is not None:
                visit.height_cm = height_cm
            if weight_kg is not None:
                visit.weight_kg = weight_kg
            if temp_c is not None:
                visit.temp_c = temp_c
            if bp_systolic is not None:
                visit.bp_systolic = bp_systolic
            if bp_diastolic is not None:
                visit.bp_diastolic = bp_diastolic
            if blood_sugar_bf is not None:
                visit.blood_sugar_bf = blood_sugar_bf
            if blood_sugar_af is not None:
                visit.blood_sugar_af = blood_sugar_af
            if pulse is not None:
                visit.pulse = pulse
            if resp_rate is not None:
                visit.resp_rate = resp_rate
            if spo2 is not None:
                visit.spo2 = spo2

            db.commit()
            db.refresh(visit)

            return {"message": "Vitals updated"}

    def delete_vitals(self, visit_id):
        with SessionLocal() as db:
            visit = self._get_visit_scoped(db, visit_id)

            if not visit:
                raise HTTPException(404, "Visit not found")

            visit.height_cm = None
            visit.weight_kg = None
            visit.temp_c = None
            visit.bp_systolic = None
            visit.bp_diastolic = None
            visit.pulse = None
            visit.resp_rate = None
            visit.spo2 = None

            db.commit()

            return {"message": "Vitals cleared"}


