# payload ={'sub': '2', 'email': 'lucky@gmail.com',
#  'roles': ['superadmin', 'admin', 'accountant', 'doctor', 'receptionist', 'nurse', 'pharmacy_admin', 'pathology_admin',
#            'radiology_admin'], 'hid': 3, 'bid': 1, 'exp': 1757508155}
#
# id  = int(payload.get("sub"))
# print(id)

#
# # app/services/admin_people.py
# from __future__ import annotations
#
# from typing import Iterable
# from fastapi import HTTPException
# from passlib.context import CryptContext
# from sqlalchemy import select, text
# from sqlalchemy.orm import Session
#
# from app.utils.tenant import Tenant
# from app.models.auth import User, Role
# from app.models.people import (
#     Patient, Staff, Doctor,
#     PatientBranchCode, StaffBranch, DoctorBranch,
# )
# from app.core.idgen import next_code, PREFIX_PATIENT, PREFIX_STAFF, PREFIX_DOCTOR
#
#
# pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
# ALLOWED_STAFF_ROLES = {
#     "receptionist", "front_office", "pharmacist", "pathologist",
#     "radiologist", "accountant", "nurse", "admin", "branch_admin",
#     "pharmacy_admin", "pathology_admin", "radiology_admin", "doctor",
# }
#
# def _role_ids(db: Session, role_names: Iterable[str]) -> dict[str, int]:
#     names = [r for r in role_names]
#     if not names:
#         return {}
#     rows = db.execute(select(Role.id, Role.name).where(Role.name.in_(names))).all()
#     # rows = [(id, name), ...]
#     found_by_name = {name: rid for rid, name in rows}
#     missing = [n for n in names if n not in found_by_name]
#     if missing:
#         raise HTTPException(status_code=400, detail=f"Unknown roles: {', '.join(missing)}")
#     return found_by_name
#
# def _ensure_email_unique(db: Session, email: str):
#     if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Email already exists")
#
#
# class AdminPeopleService:
#     def __init__(self, db: Session, tenant: Tenant) -> None:
#         self.db = db
#         self.tenant = tenant
#
#     def _apply_tenant(self, obj, *, branch_id: int | None = None):
#         # Works with any model that has these attrs
#         if hasattr(obj, "hospital_id"):
#             obj.hospital_id = self.tenant.hospital_id
#         if hasattr(obj, "branch_id"):
#             obj.branch_id = branch_id or self.tenant.branch_id
#
#     def create_patient(self, payload):
#         p = Patient(
#             first_name=payload.first_name,
#             last_name=payload.last_name,
#             dob=payload.dob,
#             phone=payload.phone or "",
#             patient_uid=next_code(self.db, PREFIX_PATIENT),  # unique per hospital
#             patient_code=next_code(self.db, PREFIX_PATIENT),  # unique per branch (ok even if column exists)
#         )
#         self._apply_tenant(p)  # sets hospital_id (+ branch_id if column exists)
#         self.db.add(p)
#         self.db.commit()
#         self.db.refresh(p)
#         return p
#
#
#     def create_doctor(self, payload):
#         st = Staff(first_name=payload.first_name, last_name=payload.last_name)
#         self._apply_tenant(st)
#         self.db.add(st)
#         self.db.flush()
#         st.staff_code = next_code(self.db, PREFIX_STAFF)
#
#         doc = Doctor(
#             staff_id=st.id,
#             consultation_fee=int(payload.consultation_fee or 0),
#             specialty=payload.specialty or "",
#             doctor_code=next_code(self.db, PREFIX_DOCTOR),
#         )
#         self._apply_tenant(doc)
#         self.db.add(doc);
#         self.db.flush()
#
#         user_id = None
#         if payload.create_user:
#             if not payload.email or not payload.password:
#                 raise HTTPException(400, "email & password required when create_user=true")
#             _ensure_email_unique(self.db, payload.email)
#
#             u = User(
#                 email=payload.email,
#                 phone=payload.phone,
#                 password_hash=pwd.hash(payload.password),
#                 is_active=True,
#                 hospital_id=self.tenant.hospital_id,
#                 current_branch_id=self.tenant.branch_id,
#             )
#             self.db.add(u);
#             self.db.flush()
#             user_id = u.id
#             rid = _role_ids(self.db, ["doctor"])["doctor"]
#             self.db.execute(text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
#                             {"u": user_id, "r": rid})
#             st.user_id = user_id
#
#         self.db.commit()
#         return {
#             "doctor_id": doc.id, "doctor_code": doc.doctor_code,
#             "staff_id": st.id, "staff_code": st.staff_code,
#             "user_id": user_id,
#         }
#
#     def create_staff(self, payload):
#         if payload.role_name == "doctor":
#             raise HTTPException(400, "Use /admin/doctors to create doctor staff")
#
#         st = Staff(first_name=payload.first_name, last_name=payload.last_name)
#         self._apply_tenant(st)  # sets hospital_id & branch_id
#         self.db.add(st)
#         self.db.flush()
#         st.staff_code = next_code(self.db, PREFIX_STAFF)
#
#         user_id = None
#         if payload.create_user:
#             if not payload.email or not payload.password:
#                 raise HTTPException(400, "email & password required when create_user=true")
#             _ensure_email_unique(self.db, payload.email)
#
#             u = User(
#                 email=payload.email,
#                 phone=payload.phone,
#                 password_hash=pwd.hash(payload.password),
#                 is_active=True,
#                 hospital_id=self.tenant.hospital_id,
#                 current_branch_id=self.tenant.branch_id,
#             )
#             self.db.add(u);
#             self.db.flush()
#             user_id = u.id
#             rid = _role_ids(self.db, [payload.role_name])[payload.role_name]
#             self.db.execute(text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
#                             {"u": user_id, "r": rid})
#             st.user_id = user_id
#
#         self.db.commit()
#         return {"staff_id": st.id, "staff_code": st.staff_code, "role_name": payload.role_name, "user_id": user_id}
#
#     # ---------------------------------------------------------------------
#     # Users / Roles (raw)
#     # ---------------------------------------------------------------------
#     def create_user(self, payload):
#         _ensure_email_unique(self.db, payload.email)
#         u = User(
#             email=payload.email,
#             phone=payload.phone,
#             password_hash=pwd.hash(payload.password),
#             is_active=True,
#             hospital_id=self.tenant.hospital_id,
#             current_branch_id=self.tenant.branch_id,
#         )
#         self.db.add(u)
#         self.db.flush()
#
#         rids = _role_ids(self.db, payload.roles)
#         for rid in rids.values():
#             self.db.execute(
#                 text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
#                 {"u": u.id, "r": rid},
#             )
#
#         self.db.commit()
#         return {
#             "id": u.id,
#             "email": u.email,
#             "is_active": u.is_active,
#             "roles": sorted(list(rids.keys())),
#         }
#
#     def set_user_roles(self, user_id: int, roles: list[str]):
#         if not self.db.get(User, user_id):
#             raise HTTPException(status_code=404, detail="User not found")
#         rids = _role_ids(self.db, roles)
#         self.db.execute(text("DELETE FROM user_roles WHERE user_id=:u"), {"u": user_id})
#         for rid in rids.values():
#             self.db.execute(
#                 text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
#                 {"u": user_id, "r": rid},
#             )
#         self.db.commit()
#         return {"user_id": user_id, "roles": sorted(list(rids.keys()))}




#
#
#
#
# notes:feaver
# shift:morning
# priority:Normal
# cash_100:0
# patient_name:raju thota
# doctor_fee:1116
# is_video:false
# cash_200:0
# cash_50:0
# cash_500:0
# cash_20:0
# doctor_name:vasu basam
# cash_10:0
# referral_name:mahesh
# utr_no:utr1234567890
# visit_type:first time
# department:cardiology
# status:booked
# slot_label:09:00-09:30
# patient_id:2
# scheduled_for:2025-09-11T10:00
# referral_amount:200
# doctor_id:4
# payment_mode:UPI
#
# {
#   "patient_id": 2,
#   "doctor_id": 4,
#   "scheduled_for": "2025-09-11T09:30",
#   "visit_type": "first time",
#   "shift": "morning",
#   "slot_label": "09:00-09:30",
#   "priority": "Normal",
#   "payment_mode": "UPI",
#   "doctor_fee": 1116,
#   "discount_pct": 0,
#   "is_video": false,
#   "status": "booked",
#   "notes": "string",
#   "cash_500": 0,
#   "cash_200": 0,
#   "cash_100": 0,
#   "cash_50": 0,
#   "cash_20": 0,
#   "cash_10": 0,
#   "utr_no": "utr1234567890"
# }
#
#
#
#

# import qrcode
#
# def create_qr_code(url, filename="qr.png"):
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(url)
#     qr.make(fit=True)
#
#     img = qr.make_image(fill_color="black", back_color="white")
#     img.save(filename)
#     return filename
#
# create_qr_code("https://onestep-medi.s3.amazonaws.com/profile_pics/ed825150-a5c2-4edf-8c65-c2aebe10f313_3.jpg")

#
# import qrcode
# print(qrcode.__file__)
# print(dir(qrcode))


# import qrcode
#
# img = qrcode.make("https://onestep-medi.s3.amazonaws.com/profile_pics/ed825150-a5c2-4edf-8c65-c2aebe10f313_3.jpg")
# img.save("qr.png")


# import qrcode
#
# print(dir(qrcode))  # should now include 'make', 'QRCode'
#
# img = qrcode.make("https://onestep-medi.s3.amazonaws.com/profile_pics/ed825150-a5c2-4edf-8c65-c2aebe10f313_3.jpg")
# img.save("qr.png")
#
#
# error occuered 99999999999 (pymysql.err.IntegrityError) (1048, "Column 'age' cannot be null")
# [SQL: INSERT INTO appointments (appointment_no, hospital_id, branch_id, patient_id, doctor_id, scheduled_for, status, notes, shift, slot_label, priority, payment_mode, doctor_fee, discount_pct, is_video, amount_payable, appointment_type, age, gender, ward_name, blood_group, cash_500, cash_200, cash_100, cash_50, cash_20, cash_10, cash_5, cash_2, cash_1, cash_total, utr_no, cancelled_at, cancel_reason, refund_amount, refund_mode, refund_cash_500, refund_cash_200, refund_cash_100, refund_cash_50, refund_cash_20, refund_cash_10, refund_cash_5, refund_cash_2, refund_cash_1, refund_cash_total, refund_utr_no, patient_name_snapshot, doctor_name_snapshot, department, discount_reason, referral_name, referral_amount, med_history_file_path) VALUES (%(appointment_no)s, %(hospital_id)s, %(branch_id)s, %(patient_id)s, %(doctor_id)s, %(scheduled_for)s, %(status)s, %(notes)s, %(shift)s, %(slot_label)s, %(priority)s, %(payment_mode)s, %(doctor_fee)s, %(discount_pct)s, %(is_video)s, %(amount_payable)s, %(appointment_type)s, %(age)s, %(gender)s, %(ward_name)s, %(blood_group)s, %(cash_500)s, %(cash_200)s, %(cash_100)s, %(cash_50)s, %(cash_20)s, %(cash_10)s, %(cash_5)s, %(cash_2)s, %(cash_1)s, %(cash_total)s, %(utr_no)s, %(cancelled_at)s, %(cancel_reason)s, %(refund_amount)s, %(refund_mode)s, %(refund_cash_500)s, %(refund_cash_200)s, %(refund_cash_100)s, %(refund_cash_50)s, %(refund_cash_20)s, %(refund_cash_10)s, %(refund_cash_5)s, %(refund_cash_2)s, %(refund_cash_1)s, %(refund_cash_total)s, %(refund_utr_no)s, %(patient_name_snapshot)s, %(doctor_name_snapshot)s, %(department)s, %(discount_reason)s, %(referral_name)s, %(referral_amount)s, %(med_history_file_path)s)]
#     [parameters: {'appointment_no': 'TEMP', 'hospital_id': 1, 'branch_id': 3, 'patient_id': 445, 'doctor_id': 4, 'scheduled_for': datetime.datetime(2026, 5, 5, 10, 0), 'status': 'booked', 'notes': 'string', 'shift': 'string', 'slot_label': 'string', 'priority': 'Normal', 'payment_mode': 'Cash', 'doctor_fee': 750, 'discount_pct': 0, 'is_video': 0, 'amount_payable': 750, 'appointment_type': None, 'age': None, 'gender': None, 'ward_name': None, 'blood_group': None, 'cash_500': 1, 'cash_200': 1, 'cash_100': 0, 'cash_50': 1, 'cash_20': 0, 'cash_10': 0, 'cash_5': 0, 'cash_2': 0, 'cash_1': 0, 'cash_total': 750, 'utr_no': None, 'cancelled_at': None, 'cancel_reason': None, 'refund_amount': None, 'refund_mode': None, 'refund_cash_500': 0, 'refund_cash_200': 0, 'refund_cash_100': 0, 'refund_cash_50': 0, 'refund_cash_20': 0, 'refund_cash_10': 0, 'refund_cash_5': 0, 'refund_cash_2': 0, 'refund_cash_1': 0, 'refund_cash_total': 0, 'refund_utr_no': None, 'patient_name_snapshot': 'string', 'doctor_name_snapshot': 'string', 'department': 'string', 'discount_reason': 'string', 'referral_name': 'string', 'referral_amount': 0, 'med_history_file_path': 'static/medical_history/47676c45aeaf4b5fa700bd424a44aa1e.png'}]
# (Background on this error at: https://sqlalche.me/e/20/gkpj)