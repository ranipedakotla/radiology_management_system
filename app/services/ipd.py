# # app/services/ipd.py
# from __future__ import annotations
#
# from datetime import datetime
from typing import Optional
#
# from fastapi import HTTPException
# from sqlalchemy import select, func, or_
#
# from app.db.session import SessionLocal
# from app.models.ipd import IPDAdmission, IPDTransfer, IPDDischarge
# from app.models.people import Patient, Doctor, Staff
# from app.models.ipd import Bed  # beds table
#
# # ---------- SERVICE ----------
#
# class IPDService:
#     # ---------- helpers ----------
#
#     def _admission_no(self, adm_id: int, dt: datetime) -> str:
#         return f"IPD{dt:%y%m}{adm_id:05d}"
#
    # def _staff_id_for_user(self, db, user_id: Optional[int]) -> Optional[int]:
    #     """
    #     Try to map the current user -> staff.id, but be tolerant of schema shapes:
    #     1) Staff has a user_id column
    #     2) User has a staff_id column
    #     Otherwise return None.
    #     """
    #     if not user_id:
    #         return None
    #
    #     # Case 1: Staff.user_id exists
    #     if hasattr(Staff, "user_id"):
    #         sid = db.execute(select(Staff.id).where(Staff.user_id == user_id)).scalar_one_or_none()
    #         return sid
    #
    #     # Case 2: User.staff_id exists
    #     try:
    #         from app.models.auth import User  # adjust import if your User model lives elsewhere
    #         if hasattr(User, "staff_id"):
    #             sid = db.execute(select(User.staff_id).where(User.id == user_id)).scalar_one_or_none()
    #             return sid
    #     except Exception:
    #         pass
    #
    #     # Couldn’t resolve a staff id; that’s OK.
    #     return None
#
#     def _find_bed(
#         self,
#         db,
#         *,
#         bed_id: Optional[int] = None,
#         bed_code: Optional[str] = None,
#     ) -> Optional[Bed]:
#         """Return a Bed by ID or by a human code/name like 'GF - 101' (ignoring spaces)."""
#         if bed_id:
#             return db.get(Bed, bed_id)
#
#         if bed_code:
#             raw = bed_code.strip()
#             no_space = raw.replace(" ", "")
#
#             clauses = []
#             if hasattr(Bed, "code"):
#                 clauses.append(Bed.code == raw)
#                 # also match code ignoring spaces, if DB has spaces
#                 clauses.append(func.replace(Bed.code, " ", "") == no_space)
#             if hasattr(Bed, "name"):
#                 clauses.append(Bed.name == raw)
#             if hasattr(Bed, "bed_no"):
#                 clauses.append(Bed.bed_no == raw)
#
#             if clauses:
#                 return db.execute(select(Bed).where(or_(*clauses)).limit(1)).scalar_one_or_none()
#
#         return None
#
#     def _ensure_bed_available(self, bed: Bed):
#         """Raise 400 if the bed is already marked used/occupied (when such a flag exists)."""
#         if hasattr(bed, "is_occupied") and getattr(bed, "is_occupied"):
#             raise HTTPException(status_code=400, detail="Selected bed is already occupied")
#         if hasattr(bed, "is_used") and getattr(bed, "is_used"):
#             raise HTTPException(status_code=400, detail="Selected bed is already used")
#
#     def _mark_bed(self, db, bed: Bed, *, occupied: bool):
#         """Flip occupancy/used flag if present in your schema."""
#         changed = False
#         if hasattr(bed, "is_occupied"):
#             bed.is_occupied = bool(occupied)
#             changed = True
#         if hasattr(bed, "is_used"):
#             bed.is_used = bool(occupied)
#             changed = True
#         if changed:
#             db.add(bed)
#
#     def _bed_label(self, bed: Bed) -> str:
#         return getattr(bed, "code", getattr(bed, "name", f"Bed #{bed.id}"))
#
#     # ---------- commands ----------
#
#     def admit(self, payload, created_by_user_id: Optional[int] = None) -> dict:
#         """Admit a patient. Accepts payload.bed_id OR payload.bed_code."""
#         print("payload", payload)
#         with SessionLocal() as db:
#             # Validate patient & doctor
#             patient = db.get(Patient, payload.patient_id)
#             if not patient:
#                 raise HTTPException(status_code=404, detail="Patient not found")
#
#             doctor = db.get(Doctor, payload.doctor_id)
#             if not doctor:
#                 raise HTTPException(status_code=404, detail="Doctor not found")
#
#             # Ensure no open admission
#             open_cnt = (
#                 db.execute(
#                     select(func.count())
#                     .select_from(IPDAdmission)
#                     .where(
#                         IPDAdmission.patient_id == payload.patient_id,
#                         IPDAdmission.status == "admitted",
#                     )
#                 ).scalar()
#                 or 0
#             )
#             if open_cnt:
#                 raise HTTPException(status_code=400, detail="Patient already has an active admission")
#
#             # Resolve bed
#             bed = self._find_bed(
#                 db,
#                 bed_id=getattr(payload, "bed_id", None),
#                 bed_code=getattr(payload, "bed_code", None),
#             )
#             if not bed:
#                 raise HTTPException(status_code=404, detail="Bed not found")
#             self._ensure_bed_available(bed)
#
#             dt = getattr(payload, "admit_datetime", None) or datetime.utcnow()
#             print("payload",payload)
#             adm = IPDAdmission(
#                 admission_no="TEMP",
#                 patient_id=payload.patient_id,
#                 doctor_id=payload.doctor_id,
#                 bed_id=bed.id,
#                 admit_datetime=dt,
#                 reason=getattr(payload, "reason", None),
#                 status="admitted",
#                 # created_by_staff_id=self._staff_id_for_user(db, created_by_user_id),
#                 created_by_user_id=created_by_user_id,
#                 current_bed=payload.bed_code,
#
#             )
#             db.add(adm)
#             db.flush()
#
#             adm.admission_no = self._admission_no(adm.id, dt)
#             self._mark_bed(db, bed, occupied=True)
#
#             db.commit()
#             db.refresh(adm)
#
#             # names for output
#             d_staff = db.get(Staff, doctor.staff_id) if getattr(doctor, "staff_id", None) else None
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "patient_name": f"{patient.first_name} {patient.last_name}".strip(),
#                 "doctor_name": f"{getattr(d_staff, 'first_name', 'Doctor')} {getattr(d_staff, 'last_name', '')}".strip(),
#                 "status": adm.status,
#                 "admit_datetime": adm.admit_datetime,
#                 "bed_id": bed.id,
#                 "bed_label": self._bed_label(bed),
#                 "reason": adm.reason,
#                 "bed_code": getattr(bed, "code", None),
#             }
#
#     def transfer(self, admission_id: int, payload, created_by_user_id: Optional[int] = None) -> dict:
#         """Transfer to another bed. Accepts payload.to_bed_id OR payload.to_bed_code."""
#         with SessionLocal() as db:
#             adm = db.get(IPDAdmission, admission_id)
#             if not adm:
#                 raise HTTPException(status_code=404, detail="Admission not found")
#             if adm.status != "admitted":
#                 raise HTTPException(status_code=400, detail="Only active admissions can be transferred")
#
#             from_bed = db.get(Bed, adm.bed_id) if adm.bed_id else None
#
#             to_bed = self._find_bed(
#                 db,
#                 bed_id=getattr(payload, "to_bed_id", None),
#                 bed_code=getattr(payload, "to_bed_code", None),
#             )
#             if not to_bed:
#                 raise HTTPException(status_code=404, detail="Target bed not found")
#             if from_bed and to_bed.id == from_bed.id:
#                 raise HTTPException(status_code=400, detail="Already in the specified bed")
#
#             self._ensure_bed_available(to_bed)
#
#             tr_dt = getattr(payload, "transfer_datetime", None) or datetime.utcnow()
#             tr = IPDTransfer(
#                 admission_id=adm.id,
#                 from_bed_id=adm.bed_id,
#                 to_bed_id=to_bed.id,
#                 transfer_datetime=tr_dt,
#                 notes=getattr(payload, "notes", None),
#                 # created_by_staff_id=self._staff_id_for_user(db, created_by_user_id),
#                 created_by_user_id=created_by_user_id,
#             )
#             db.add(tr)
#
#             adm.bed_id = to_bed.id
#             if from_bed:
#                 self._mark_bed(db, from_bed, occupied=False)
#             self._mark_bed(db, to_bed, occupied=True)
#
#             db.commit()
#             db.refresh(adm)
#
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "status": adm.status,
#                 "bed_id": adm.bed_id,
#                 "bed_label": self._bed_label(to_bed),
#                 "transfer_datetime": tr_dt,
#             }
#
    # def discharge(self, admission_id: int, payload, created_by_user_id: Optional[int] = None) -> dict:
    #     with SessionLocal() as db:
    #         adm = db.get(IPDAdmission, admission_id)
    #         print("%%%%%%%%%%%",adm.status)
    #         if not adm:
    #             raise HTTPException(status_code=404, detail="Admission not found")
    #         if adm.status != "admitted":
    #             raise HTTPException(status_code=400, detail="Admission already discharged")
    #
    #         print("payload",payload.summary)
    #
    #         dd = getattr(payload, "discharge_datetime", None) or datetime.utcnow()
    #         dc = IPDDischarge(
    #             admission_id=adm.id,
    #             discharge_datetime=dd,
    #             outcome=getattr(payload, "outcome", None),
    #             summary=getattr(payload, "summary", None),
    #             advice=getattr(payload, "advice", None),
    #             # created_by_staff_id=self._staff_id_for_user(db, created_by_user_id),
    #             # created_by_user_id=self._staff_id_for_user(db, created_by_user_id),
    #             created_by_user_id=created_by_user_id,
    #
    #         )
    #
    #         db.add(dc)
    #
    #         if adm.bed_id:
    #             bed = db.get(Bed, adm.bed_id)
    #             if bed:
    #                 self._mark_bed(db, bed, occupied=False)
    #         print(adm)
    #
    #         adm.status = "discharged"
    #         db.commit()
    #         db.refresh(adm)
    #         # print("1",adm.id)
    #         # print("2",adm.admission_no)
    #         # print("3",adm.admit_datetime)
    #         # print("4",adm.patient.name if adm.patient else None)
    #         # print("5",adm.doctor.name if adm.doctor else None)
    #         # print("6",adm.bed.id if adm.bed else None)
    #         # print("7",adm.bed.code if adm.bed else None)
    #         # print("8",adm.status)
    #         # print("9",dd)
    #         # print("10",dc.outcome)
    #         return {
    #             "id": adm.id,
    #             "admission_no": adm.admission_no,
    #             "admit_datetime": adm.admit_datetime,
    #             "patient_name": adm.patient_id,
    #             "doctor_name": adm.doctor_id,
    #             "bed_id": adm.bed.id if adm.bed else None,
    #             "bed_code": adm.bed.code if adm.bed else None,
    #             "status": adm.status,
    #             "discharge_datetime": dd,
    #             "outcome": dc.outcome,
    #         }
    #
    #         # return {
    #         #     "id": adm.id,
    #         #     "admission_no": adm.admission_no,
    #         #     "status": adm.status,
    #         #     "discharge_datetime": dd,
    #         #     "outcome": dc.outcome,
    #         # }

#     # ---------- queries ----------
#
#     def list_admissions(
#         self,
#         status: Optional[str],
#         patient_id: Optional[int],
#         doctor_id: Optional[int],
#         page: int,
#         page_size: int,
#     ) -> tuple[list[dict], int]:
#         with SessionLocal() as db:
#             stmt = (
#                 select(
#                     IPDAdmission,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                     Staff.first_name.label("d_fn"),
#                     Staff.last_name.label("d_ln"),
#                     Bed.code.label("bed_code"),
#                 )
#                 .join(Patient, Patient.id == IPDAdmission.patient_id)
#                 .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
#                 .join(Staff, Staff.id == Doctor.staff_id)
#                 .outerjoin(Bed, Bed.id == IPDAdmission.bed_id)
#             )
#             if status:
#                 stmt = stmt.where(IPDAdmission.status == status)
#             if patient_id:
#                 stmt = stmt.where(IPDAdmission.patient_id == patient_id)
#             if doctor_id:
#                 stmt = stmt.where(IPDAdmission.doctor_id == doctor_id)
#
#             total = int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0)
#             rows = db.execute(
#                 stmt.order_by(IPDAdmission.admit_datetime.desc())
#                 .offset((page - 1) * page_size)
#                 .limit(page_size)
#             ).all()
#
#             items: list[dict] = []
#             for row in rows:
#                 adm: IPDAdmission = row[0]
#                 items.append(
#                     {
#                         "id": adm.id,
#                         "admission_no": adm.admission_no,
#                         "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
#                         "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
#                         "status": adm.status,
#                         "admit_datetime": adm.admit_datetime,
#                         "bed_id": adm.bed_id,
#                         "bed_label": row.bed_code or (f"Bed #{adm.bed_id}" if adm.bed_id else None),
#                     }
#                 )
#             return items, total
#
#     def get_admission(self, admission_id: int) -> dict:
#         with SessionLocal() as db:
#             row = db.execute(
#                 select(
#                     IPDAdmission,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                     Staff.first_name.label("d_fn"),
#                     Staff.last_name.label("d_ln"),
#                     Bed.code.label("bed_code"),
#                 )
#                 .join(Patient, Patient.id == IPDAdmission.patient_id)
#                 .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
#                 .join(Staff, Staff.id == Doctor.staff_id)
#                 .outerjoin(Bed, Bed.id == IPDAdmission.bed_id)
#                 .where(IPDAdmission.id == admission_id)
#             ).first()
#
#             if not row:
#                 raise HTTPException(status_code=404, detail="Admission not found")
#
#             adm: IPDAdmission = row[0]
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
#                 "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
#                 "status": adm.status,
#                 "admit_datetime": adm.admit_datetime,
#                 "bed_id": adm.bed_id,
#                 "bed_label": row.bed_code or (f"Bed #{adm.bed_id}" if adm.bed_id else None),
#                 "reason": adm.reason,
#             }

# app/services/ipd.py
# from __future__ import annotations
#
# from datetime import datetime
# from fastapi import HTTPException
# from sqlalchemy import select, func
# from sqlalchemy.orm import joinedload
#
# from app.db.session import SessionLocal
# from app.models.ipd import (
#     IPDAdmission, IPDTransfer, IPDDischarge,
#     Bed, BedGroup, Floor, BedOccupancy,
# )
# from app.models.people import Patient, Doctor, Staff
#
#
# class IPDService:
#     # map a logged-in user -> staff.id (or None if not linked)
#     def _staff_id_for_user(self, db, user_id: int | None) -> int | None:
#         if not user_id:
#             return None
#         st = db.execute(
#             select(Staff).where(Staff.user_id == user_id)
#         ).scalar_one_or_none()
#         return st.id if st else None
#
#     def _admission_no(self, adm_id: int, dt: datetime) -> str:
#         return f"IPD{dt:%y%m}{adm_id:05d}"
#
#     def _load_bed(
#         self, db, *, bed_id: int | None = None, bed_code: str | None = None
#     ) -> Bed:
#         if not bed_id and not bed_code:
#             raise HTTPException(status_code=400, detail="Provide bed_id or bed_code")
#
#         # q = select(Bed).options(
#         #     joinedload(Bed.bed_group).joinedload(Bed.bed_group.floor),
#         #     joinedload(Bed.bed_type),
#         # )
#         q = select(Bed).options(
#             joinedload(Bed.bed_group).joinedload(BedGroup.floor),
#             joinedload(Bed.bed_type),
#         )
#
#
#         if bed_id:
#             q = q.where(Bed.id == bed_id)
#         else:
#             q = q.where(Bed.code == bed_code)
#
#         bed = db.execute(q).scalar_one_or_none()
#         if not bed:
#             raise HTTPException(status_code=404, detail="Bed not found")
#         return bed
#
#     def _patient(self, db, pid: int) -> Patient:
#         p = db.get(Patient, pid)
#         if not p:
#             raise HTTPException(status_code=404, detail="Patient not found")
#         return p
#
#     def _doctor(self, db, did: int) -> Doctor:
#         d = db.get(Doctor, did)
#         if not d:
#             raise HTTPException(status_code=404, detail="Doctor not found")
#         return d
#
#
#     # ---------- core ops ----------
#
#     def admit(self, payload, created_by_user_id: int | None = None) -> dict:
#         """
#         payload supports either:
#           - {patient_id, doctor_id, bed_id,   admit_datetime?, reason?}
#           - {patient_id, doctor_id, bed_code, admit_datetime?, reason?}
#         """
#         with SessionLocal() as db:
#             self._patient(db, payload.patient_id)
#             doc = self._doctor(db, payload.doctor_id)
#
#             # prevent duplicate active admission for the same patient
#             open_cnt = db.execute(
#                 select(func.count()).where(
#                     IPDAdmission.patient_id == payload.patient_id,
#                     IPDAdmission.status == "admitted",
#                 )
#             ).scalar() or 0
#             if open_cnt:
#                 raise HTTPException(status_code=400, detail="Patient already admitted")
#
#             # bed lookup & guard
#             bed = self._load_bed(
#                 db,
#                 bed_id=getattr(payload, "bed_id", None),
#                 bed_code=getattr(payload, "bed_code", None),
#             )
#             if bed.is_occupied:
#                 raise HTTPException(status_code=400, detail=f"Bed {bed.code} is already occupied")
#
#             dt = getattr(payload, "admit_datetime", None) or datetime.utcnow()
#
#             # snapshot for convenience/reporting
#             ward_name = bed.bed_group.name if bed.bed_group else None
#             room_name = None  # you can map a "room" if you store it elsewhere
#             bed_name = bed.code
#
#             adm = IPDAdmission(
#                 admission_no="TEMP",
#                 patient_id=payload.patient_id,
#                 doctor_id=payload.doctor_id,
#                 bed_id=bed.id,
#                 admit_datetime=dt,
#                 reason=getattr(payload, "reason", None),
#                 status="admitted",
#                 current_ward=ward_name,
#                 current_room=room_name,
#                 current_bed=bed_name,
#                 created_by_user_id=created_by_user_id,
#             )
#             db.add(adm)
#             db.flush()
#
#             # finalize admission no
#             adm.admission_no = self._admission_no(adm.id, dt)
#
#             # mark bed occupied + start occupancy interval
#             bed.is_occupied = True
#             db.add(BedOccupancy(admission_id=adm.id, bed_id=bed.id, start=dt))
#
#             db.commit()
#             db.refresh(adm)
#
#             # names for output
#             d_staff = db.get(Staff, doc.staff_id) if doc.staff_id else None
#             pat = db.get(Patient, payload.patient_id)
#
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "patient_name": f"{pat.first_name} {pat.last_name}".strip() if pat else "",
#                 "doctor_name": f"{d_staff.first_name} {d_staff.last_name}".strip() if d_staff else "",
#                 "status": adm.status,
#                 "admit_datetime": adm.admit_datetime,
#                 "bed_id": adm.bed_id,
#                 "bed_code": bed.code,
#                 "current_ward": adm.current_ward,
#                 "current_room": adm.current_room,
#                 "current_bed": adm.current_bed,
#                 "reason": adm.reason,
#             }
#
#     def transfer(self, admission_id: int, payload, created_by_user_id: int | None = None) -> dict:
#         """
#         payload supports either:
#           - {to_bed_id, transfer_datetime?, reason?}
#           - {to_bed_code, transfer_datetime?, reason?}
#         """
#         with SessionLocal() as db:
#             adm = db.get(IPDAdmission, admission_id)
#             if not adm:
#                 raise HTTPException(status_code=404, detail="Admission not found")
#             if adm.status != "admitted":
#                 raise HTTPException(status_code=400, detail="Only active admissions can be transferred")
#
#             to_bed = self._load_bed(
#                 db,
#                 bed_id=getattr(payload, "to_bed_id", None),
#                 bed_code=getattr(payload, "to_bed_code", None),
#             )
#             if to_bed.is_occupied:
#                 raise HTTPException(status_code=400, detail=f"Bed {to_bed.code} is already occupied")
#
#             when = getattr(payload, "transfer_datetime", None) or datetime.utcnow()
#
#             # end current occupancy interval
#             occ = db.execute(
#                 select(BedOccupancy)
#                 .where(BedOccupancy.admission_id == adm.id, BedOccupancy.end.is_(None))
#                 .order_by(BedOccupancy.start.desc())
#             ).scalars().first()
#             if occ:
#                 occ.end = when
#
#             # free old bed, occupy new bed
#             old_bed = db.get(Bed, adm.bed_id)
#             if old_bed:
#                 old_bed.is_occupied = False
#             to_bed.is_occupied = True
#
#             # create new occupancy interval
#             db.add(BedOccupancy(admission_id=adm.id, bed_id=to_bed.id, start=when))
#
#             # record transfer
#             db.add(IPDTransfer(
#                 admission_id=adm.id,
#                 from_bed_id=adm.bed_id,
#                 to_bed_id=to_bed.id,
#                 transfer_datetime=when,
#                 reason=getattr(payload, "reason", None),
#             ))
#
#             # update admission snapshot
#             adm.bed_id = to_bed.id
#             adm.current_ward = to_bed.bed_group.name if to_bed.bed_group else None
#             adm.current_room = None
#             adm.current_bed = to_bed.code
#
#             db.commit()
#             db.refresh(adm)
#
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "status": adm.status,
#                 "bed_id": adm.bed_id,
#                 "bed_code": to_bed.code,
#                 "current_ward": adm.current_ward,
#                 "current_room": adm.current_room,
#                 "current_bed": adm.current_bed,
#             }
#
#
#
#
#     # def discharge(self, admission_id: int, payload, created_by_user_id: int | None = None) -> dict:
#     #     """
#     #     payload: {discharge_datetime?, outcome?, notes?, summary?, advice?}
#     #     """
#     #     with SessionLocal() as db:
#     #         adm = db.get(IPDAdmission, admission_id)
#     #         if not adm:
#     #             raise HTTPException(status_code=404, detail="Admission not found")
#     #         if adm.status != "admitted":
#     #             raise HTTPException(status_code=400, detail="Admission already discharged")
#     #
#     #         when = getattr(payload, "discharge_datetime", None) or datetime.utcnow()
#     #
#     #         # end last occupancy
#     #         occ = db.execute(
#     #             select(BedOccupancy)
#     #             .where(BedOccupancy.admission_id == adm.id, BedOccupancy.end.is_(None))
#     #             .order_by(BedOccupancy.start.desc())
#     #         ).scalars().first()
#     #         if occ:
#     #             occ.end = when
#     #
#     #         # free the bed
#     #         bed = db.get(Bed, adm.bed_id)
#     #         if bed:
#     #             bed.is_occupied = False
#     #
#     #         # record discharge
#     #         db.add(IPDDischarge(
#     #             admission_id=adm.id,
#     #             discharge_datetime=when,
#     #             outcome=getattr(payload, "outcome", "recovered"),
#     #             notes=getattr(payload, "notes", None),
#     #             summary=getattr(payload, "summary", None),
#     #             advice=getattr(payload, "advice", None),
#     #             created_by_user_id=created_by_user_id,
#     #         ))
#     #         adm.status = "discharged"
#     #
#     #         db.commit()
#     #         db.refresh(adm)
#     #         return {
#     #             "id": adm.id,
#     #             "admission_no": adm.admission_no,
#     #             "status": adm.status,
#     #             "discharge_datetime": when,
#     #             "outcome": "recovered" if not getattr(payload, "outcome", None) else payload.outcome,
#     #         }
#
#     # replace your current discharge() with this
#     def discharge(self, admission_id: int, payload, created_by_user_id: int | None = None) -> dict:
#         from datetime import datetime
#         with SessionLocal() as db:
#             adm = db.get(IPDAdmission, admission_id)
#             if not adm:
#                 raise HTTPException(status_code=404, detail="Admission not found")
#             if adm.status != "admitted":
#                 raise HTTPException(status_code=400, detail="Admission already discharged")
#
#             # 1) create discharge record
#             dd = payload.discharge_datetime or datetime.utcnow()
#             dc = IPDDischarge(
#                 admission_id=adm.id,
#                 discharge_datetime=dd,
#                 outcome=payload.outcome,
#                 summary=getattr(payload, "summary", None),
#                 advice=getattr(payload, "advice", None),
#                 created_by_staff_id=self._staff_id_for_user(db, created_by_user_id),
#             )
#             db.add(dc)
#
#             # 2) close the open bed occupancy (if any)
#             occ = db.execute(
#                 select(BedOccupancy)
#                 .where(
#                     BedOccupancy.admission_id == adm.id,
#                     BedOccupancy.end.is_(None),
#                 )
#                 .order_by(BedOccupancy.start.desc())
#             ).scalars().first()
#             if occ:
#                 occ.end = dd
#
#             # 3) free the bed (if the column exists)
#             if adm.bed_id:
#                 bed = db.get(Bed, adm.bed_id)
#                 if bed is not None:
#                     # your schema shows a "Used" checkmark; in your model it may be `used` or `is_used`
#                     if hasattr(bed, "used"):
#                         bed.used = False
#                     elif hasattr(bed, "is_used"):
#                         bed.is_used = False
#
#             # 4) mark admission as discharged
#             adm.status = "discharged"
#             db.commit()
#             db.refresh(adm)
#
#             # 5) build the response that matches AdmissionOut
#             #    (join to get names + the bed code/name)
#             row = db.execute(
#                 select(
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                     Staff.first_name.label("d_fn"),
#                     Staff.last_name.label("d_ln"),
#                     Bed.name.label("bed_code"),  # if your column is Bed.code, change this line
#                 )
#                 .join(Patient, Patient.id == adm.patient_id)
#                 .join(Doctor, Doctor.id == adm.doctor_id)
#                 .join(Staff, Staff.id == Doctor.staff_id)
#                 .outerjoin(Bed, Bed.id == adm.bed_id)
#             ).first()
#
#             patient_name = f"{row.p_fn} {row.p_ln}".strip() if row else ""
#             doctor_name = f"{row.d_fn} {row.d_ln}".strip() if row else ""
#             bed_code = row.bed_code if row else None
#
#             # IMPORTANT: return exactly the fields your AdmissionOut requires
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "patient_name": patient_name,
#                 "doctor_name": doctor_name,
#                 "status": adm.status,
#                 "admit_datetime": adm.admit_datetime,
#                 "bed_id": adm.bed_id,
#                 "bed_code": bed_code,
#             }
#
#
#     # ---------- queries ----------
#
#     def list_admissions(self, status: str | None, patient_id: int | None, doctor_id: int | None,
#                         page: int, page_size: int) -> tuple[list[dict], int]:
#         with SessionLocal() as db:
#             stmt = (
#                 select(
#                     IPDAdmission,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                     Staff.first_name.label("d_fn"),
#                     Staff.last_name.label("d_ln"),
#                     Bed.code.label("bed_code"),
#                 )
#                 .join(Patient, Patient.id == IPDAdmission.patient_id)
#                 .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
#                 .join(Staff, Staff.id == Doctor.staff_id)
#                 .join(Bed, Bed.id == IPDAdmission.bed_id)
#             )
#             if status:
#                 stmt = stmt.where(IPDAdmission.status == status)
#             if patient_id:
#                 stmt = stmt.where(IPDAdmission.patient_id == patient_id)
#             if doctor_id:
#                 stmt = stmt.where(IPDAdmission.doctor_id == doctor_id)
#
#             total = int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0)
#             rows = db.execute(
#                 stmt.order_by(IPDAdmission.admit_datetime.desc())
#                     .offset((page - 1) * page_size)
#                     .limit(page_size)
#             ).all()
#
#             items: list[dict] = []
#             for row in rows:
#                 adm: IPDAdmission = row[0]
#                 items.append({
#                     "id": adm.id,
#                     "admission_no": adm.admission_no,
#                     "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
#                     "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
#                     "status": adm.status,
#                     "admit_datetime": adm.admit_datetime,
#                     "bed_code": row.bed_code,
#                     "current_ward": adm.current_ward,
#                     "current_room": adm.current_room,
#                     "current_bed": adm.current_bed,
#                 })
#             return items, total
#
#     def get_admission(self, admission_id: int) -> dict:
#         with SessionLocal() as db:
#             row = db.execute(
#                 select(
#                     IPDAdmission,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                     Staff.first_name.label("d_fn"),
#                     Staff.last_name.label("d_ln"),
#                     Bed.code.label("bed_code"),
#                 )
#                 .join(Patient, Patient.id == IPDAdmission.patient_id)
#                 .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
#                 .join(Staff, Staff.id == Doctor.staff_id)
#                 .join(Bed, Bed.id == IPDAdmission.bed_id)
#                 .where(IPDAdmission.id == admission_id)
#             ).first()
#             if not row:
#                 raise HTTPException(status_code=404, detail="Admission not found")
#
#             adm: IPDAdmission = row[0]
#             return {
#                 "id": adm.id,
#                 "admission_no": adm.admission_no,
#                 "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
#                 "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
#                 "status": adm.status,
#                 "admit_datetime": adm.admit_datetime,
#                 "bed_id": adm.bed_id,
#                 "bed_code": row.bed_code,
#                 "current_ward": adm.current_ward,
#                 "current_room": adm.current_room,
#                 "current_bed": adm.current_bed,
#                 "reason": adm.reason,
#             }
#



# app/services/ipd.py
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.ipd import IPDAdmission, IPDTransfer, IPDDischarge, Bed, BedGroup, BedOccupancy
from app.models.people import Patient, Doctor, Staff
from app.utils.tenant import Tenant
from app.services._tenant_utils import _set_tenant_fields, _filter_by_tenant, _get_by_id_scoped

class IPDService:
    def _admission_no(self, adm_id: int, dt: datetime) -> str:
        return f"IPD{dt:%y%m}{adm_id:05d}"

    def _load_bed(self, db, *, bed_id: int | None = None, bed_code: str | None = None, tenant: Tenant) -> Bed:
        if not bed_id and not bed_code:
            raise HTTPException(status_code=400, detail="Provide bed_id or bed_code")
        q = select(Bed).options(
            joinedload(Bed.bed_group).joinedload(BedGroup.floor),
            joinedload(Bed.bed_type),
        )
        q = _filter_by_tenant(q, Bed, tenant)
        if bed_id:
            q = q.where(Bed.id == bed_id)
        else:
            q = q.where(Bed.code == bed_code)
        bed = db.execute(q).scalar_one_or_none()
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
        return bed

    # ---------- core ops ----------
    def admit(self, payload, tenant: Tenant, created_by_user_id: int | None = None) -> dict:
        with SessionLocal() as db:
            patient = _get_by_id_scoped(db, Patient, payload.patient_id, tenant)
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found")
            doc = _get_by_id_scoped(db, Doctor, payload.doctor_id, tenant)
            if not doc:
                raise HTTPException(status_code=404, detail="Doctor not found")

            open_cnt = db.execute(
                _filter_by_tenant(
                    select(func.count()).select_from(IPDAdmission)
                    .where(IPDAdmission.patient_id == payload.patient_id, IPDAdmission.status == "admitted"),
                    IPDAdmission,
                    tenant,
                )
            ).scalar() or 0
            if open_cnt:
                raise HTTPException(status_code=400, detail="Patient already admitted")

            bed = self._load_bed(
                db,
                bed_id=getattr(payload, "bed_id", None),
                bed_code=getattr(payload, "bed_code", None),
                tenant=tenant,
            )
            if getattr(bed, "is_occupied", False):
                raise HTTPException(status_code=400, detail=f"Bed {bed.code} is already occupied")

            dt = getattr(payload, "admit_datetime", None) or datetime.utcnow()
            adm = IPDAdmission(
                admission_no="TEMP",
                patient_id=patient.id,
                doctor_id=doc.id,
                bed_id=bed.id,
                admit_datetime=dt,
                reason=getattr(payload, "reason", None),
                status="admitted",
                current_ward=bed.bed_group.name if bed.bed_group else None,
                current_room=None,
                current_bed=bed.code,
                created_by_user_id=created_by_user_id,
            )
            _set_tenant_fields(adm, tenant)
            db.add(adm)
            db.flush()

            adm.admission_no = self._admission_no(adm.id, dt)
            bed.is_occupied = True
            db.add(bed)

            occ = BedOccupancy(admission_id=adm.id, bed_id=bed.id, start=dt)
            _set_tenant_fields(occ, tenant)
            db.add(occ)

            db.commit()
            db.refresh(adm)

            st = _get_by_id_scoped(db, Staff, doc.staff_id, tenant) if doc.staff_id else None
            return {
                "id": adm.id,
                "admission_no": adm.admission_no,
                "patient_name": f"{patient.first_name} {patient.last_name}".strip(),
                "doctor_name": f"{getattr(st, 'first_name', '')} {getattr(st, 'last_name', '')}".strip() if st else "",
                "status": adm.status,
                "admit_datetime": adm.admit_datetime,
                "bed_id": bed.id,
                "bed_code": bed.code,
                "current_ward": adm.current_ward,
                "current_room": adm.current_room,
                "current_bed": adm.current_bed,
                "reason": adm.reason,
            }

    def transfer(self, admission_id: int, payload, tenant: Tenant, created_by_user_id: int | None = None) -> dict:
        with SessionLocal() as db:
            adm = _get_by_id_scoped(db, IPDAdmission, admission_id, tenant)
            if not adm:
                raise HTTPException(status_code=404, detail="Admission not found")
            if adm.status != "admitted":
                raise HTTPException(status_code=400, detail="Only active admissions can be transferred")

            to_bed = self._load_bed(
                db,
                bed_id=getattr(payload, "to_bed_id", None),
                bed_code=getattr(payload, "to_bed_code", None),
                tenant=tenant,
            )
            if getattr(to_bed, "is_occupied", False):
                raise HTTPException(status_code=400, detail=f"Bed {to_bed.code} is already occupied")

            when = getattr(payload, "transfer_datetime", None) or datetime.utcnow()

            # close current occupancy
            occ_stmt = select(BedOccupancy).where(BedOccupancy.admission_id == adm.id, BedOccupancy.end.is_(None)).order_by(BedOccupancy.start.desc())
            occ_stmt = _filter_by_tenant(occ_stmt, BedOccupancy, tenant)
            occ = db.execute(occ_stmt).scalars().first()
            if occ:
                occ.end = when

            # free old bed, occupy new bed
            old_bed = _get_by_id_scoped(db, Bed, adm.bed_id, tenant) if adm.bed_id else None
            if old_bed:
                old_bed.is_occupied = False
            to_bed.is_occupied = True

            db.add(IPDTransfer(
                admission_id=adm.id,
                from_bed_id=adm.bed_id,
                to_bed_id=to_bed.id,
                transfer_datetime=when,
                reason=getattr(payload, "reason", None),
            ))

            adm.bed_id = to_bed.id
            adm.current_ward = to_bed.bed_group.name if to_bed.bed_group else None
            adm.current_room = None
            adm.current_bed = to_bed.code

            new_occ = BedOccupancy(admission_id=adm.id, bed_id=to_bed.id, start=when)
            _set_tenant_fields(new_occ, tenant)
            db.add(new_occ)

            db.commit()
            db.refresh(adm)
            return {
                "id": adm.id,
                "admission_no": adm.admission_no,
                "status": adm.status,
                "bed_id": adm.bed_id,
                "bed_code": to_bed.code,
                "current_ward": adm.current_ward,
                "current_room": adm.current_room,
                "current_bed": adm.current_bed,
            }

    def discharge(self, admission_id: int, payload, tenant: Tenant, created_by_user_id: int | None = None) -> dict:
        with SessionLocal() as db:
            adm = _get_by_id_scoped(db, IPDAdmission, admission_id, tenant)
            if not adm:
                raise HTTPException(status_code=404, detail="Admission not found")
            if adm.status != "admitted":
                raise HTTPException(status_code=400, detail="Admission already discharged")

            dd = getattr(payload, "discharge_datetime", None) or datetime.utcnow()
            dc = IPDDischarge(
                admission_id=adm.id,
                discharge_datetime=dd,
                outcome=getattr(payload, "outcome", "recovered"),
                summary=getattr(payload, "summary", None),
                advice=getattr(payload, "advice", None),
                created_by_user_id=created_by_user_id,
            )
            _set_tenant_fields(dc, tenant)
            db.add(dc)

            # end occupancy
            occ_stmt = select(BedOccupancy).where(BedOccupancy.admission_id == adm.id, BedOccupancy.end.is_(None)).order_by(BedOccupancy.start.desc())
            occ_stmt = _filter_by_tenant(occ_stmt, BedOccupancy, tenant)
            occ = db.execute(occ_stmt).scalars().first()
            if occ:
                occ.end = dd

            # free bed
            if adm.bed_id:
                bed = _get_by_id_scoped(db, Bed, adm.bed_id, tenant)
                if bed:
                    bed.is_occupied = False

            adm.status = "discharged"
            db.commit()
            db.refresh(adm)

            # names for response
            p = _get_by_id_scoped(db, Patient, adm.patient_id, tenant)
            d = _get_by_id_scoped(db, Doctor, adm.doctor_id, tenant)
            st = _get_by_id_scoped(db, Staff, d.staff_id, tenant) if d and d.staff_id else None
            bed_code = _get_by_id_scoped(db, Bed, adm.bed_id, tenant).code if adm.bed_id else None

            return {
                "id": adm.id,
                "admission_no": adm.admission_no,
                "patient_name": f"{p.first_name} {p.last_name}".strip() if p else "",
                "doctor_name": f"{getattr(st,'first_name','')} {getattr(st,'last_name','')}".strip() if st else "",
                "status": adm.status,
                "admit_datetime": adm.admit_datetime,
                "bed_id": adm.bed_id,
                "bed_code": bed_code,
            }

    # ---------- queries ----------
    def list_admissions(self, status: str | None, patient_id: int | None, doctor_id: int | None, page: int, page_size: int, tenant: Tenant):
        with SessionLocal() as db:
            stmt = (
                select(
                    IPDAdmission,
                    Patient.first_name.label("p_fn"),
                    Patient.last_name.label("p_ln"),
                    Staff.first_name.label("d_fn"),
                    Staff.last_name.label("d_ln"),
                    Bed.code.label("bed_code"),
                )
                .join(Patient, Patient.id == IPDAdmission.patient_id)
                .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
                .join(Staff, Staff.id == Doctor.staff_id)
                .join(Bed, Bed.id == IPDAdmission.bed_id)
            )
            stmt = _filter_by_tenant(stmt, IPDAdmission, tenant)
            stmt = _filter_by_tenant(stmt, Patient, tenant)
            stmt = _filter_by_tenant(stmt, Doctor, tenant)
            stmt = _filter_by_tenant(stmt, Bed, tenant)

            if status:
                stmt = stmt.where(IPDAdmission.status == status)
            if patient_id:
                stmt = stmt.where(IPDAdmission.patient_id == patient_id)
            if doctor_id:
                stmt = stmt.where(IPDAdmission.doctor_id == doctor_id)

            total = int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0)
            rows = db.execute(
                stmt.order_by(IPDAdmission.admit_datetime.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
            ).all()

            items = []
            for row in rows:
                adm: IPDAdmission = row[0]
                items.append({
                    "id": adm.id,
                    "admission_no": adm.admission_no,
                    "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
                    "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
                    "status": adm.status,
                    "admit_datetime": adm.admit_datetime,
                    "bed_code": row.bed_code,
                    "current_ward": adm.current_ward,
                    "current_room": adm.current_room,
                    "current_bed": adm.current_bed,
                })
            return items, total

    def get_admission(self, admission_id: int, tenant: Tenant) -> dict:
        with SessionLocal() as db:
            stmt = (
                select(
                    IPDAdmission,
                    Patient.first_name.label("p_fn"),
                    Patient.last_name.label("p_ln"),
                    Staff.first_name.label("d_fn"),
                    Staff.last_name.label("d_ln"),
                    Bed.code.label("bed_code"),
                )
                .join(Patient, Patient.id == IPDAdmission.patient_id)
                .join(Doctor, Doctor.id == IPDAdmission.doctor_id)
                .join(Staff, Staff.id == Doctor.staff_id)
                .join(Bed, Bed.id == IPDAdmission.bed_id)
                .where(IPDAdmission.id == admission_id)
            )
            stmt = _filter_by_tenant(stmt, IPDAdmission, tenant)
            row = db.execute(stmt).first()
            if not row:
                raise HTTPException(status_code=404, detail="Admission not found")

            adm: IPDAdmission = row[0]
            return {
                "id": adm.id,
                "admission_no": adm.admission_no,
                "patient_name": f"{row.p_fn} {row.p_ln}".strip(),
                "doctor_name": f"{row.d_fn} {row.d_ln}".strip(),
                "status": adm.status,
                "admit_datetime": adm.admit_datetime,
                "bed_id": adm.bed_id,
                "bed_code": row.bed_code,
                "current_ward": adm.current_ward,
                "current_room": adm.current_room,
                "current_bed": adm.current_bed,
                "reason": adm.reason,
            }
