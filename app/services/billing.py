# from datetime import datetime
# from decimal import Decimal, ROUND_HALF_UP
# from fastapi import HTTPException
# from sqlalchemy import select, func
# from sqlalchemy.orm import joinedload
#
# from app.db.session import SessionLocal
# from app.models.billing import Invoice, InvoiceItem, Receipt
# from app.models.people import Patient
# from app.models.opd import OPDVisit
# from app.models.appointments import Appointment
# from app.utils.cash import ensure_non_negative, sum_cash
#
#
# Q = Decimal  # alias for readability
#
#
# def q2(v: Decimal | float | int) -> Decimal:
#     return Q(v).quantize(Q("0.01"), rounding=ROUND_HALF_UP)
#
#
# class BillingService:
#     def _gen_invoice_no(self, created_at: datetime, inv_id: int) -> str:
#         return f"INV{created_at:%y%m}{inv_id:05d}"
#
#     def create_invoice(self, payload):
#         with SessionLocal() as db:
#             # resolve patient by id or patient_uid
#             patient_id = payload.patient_id
#             if not patient_id and getattr(payload, "patient_uid", None):
#                 patient_id = db.execute(
#                     select(Patient.id).where(Patient.patient_uid == payload.patient_uid.strip())
#                 ).scalar_one_or_none()
#             if not patient_id:
#                 raise HTTPException(status_code=400, detail="Provide valid patient_id or patient_uid")
#
#             # Optional links
#             visit_id = payload.visit_id
#             if visit_id:
#                 if not db.get(OPDVisit, visit_id):
#                     raise HTTPException(status_code=400, detail="visit_id not found")
#
#             appointment_id = payload.appointment_id
#             if appointment_id:
#                 if not db.get(Appointment, appointment_id):
#                     raise HTTPException(status_code=400, detail="appointment_id not found")
#
#             inv = Invoice(
#                 patient_id=patient_id,
#                 visit_id=visit_id,
#                 appointment_id=appointment_id,
#                 status="draft",
#                 created_at=datetime.utcnow(),
#             )
#             db.add(inv)
#             db.flush()
#
#             # Items (optional)
#             sub_total = Q("0.00")
#             for it in payload.items or []:
#                 qty = it.qty or 1
#                 unit = q2(it.unit_price or Q("0.00"))
#                 line = q2(Q(qty) * unit)
#                 db.add(
#                     InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type=it.item_type,
#                         ref_id=it.ref_id,
#                         description=it.description,
#                         qty=qty,
#                         unit_price=unit,
#                         line_total=line,
#                     )
#                 )
#                 sub_total += line
#
#             inv.sub_total = q2(sub_total)
#             db.flush()
#
#             # generate invoice_no
#             inv.invoice_no = self._gen_invoice_no(inv.created_at, inv.id)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def add_item(self, invoice_id: int, item_payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot add items to a void invoice")
#
#             qty = item_payload.qty or 1
#             unit = q2(item_payload.unit_price or Q("0.00"))
#             line = q2(Q(qty) * unit)
#             db.add(
#                 InvoiceItem(
#                     invoice_id=invoice_id,
#                     item_type=item_payload.item_type,
#                     ref_id=item_payload.ref_id,
#                     description=item_payload.description,
#                     qty=qty,
#                     unit_price=unit,
#                     line_total=line,
#                 )
#             )
#             inv.sub_total = q2(Q(inv.sub_total) + line)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def finalize(self, invoice_id: int, payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot finalize a void invoice")
#
#             sub = q2(inv.sub_total)
#             # discount
#             if payload.discount_amount is not None:
#                 disc_amt = q2(payload.discount_amount)
#             elif payload.discount_pct is not None:
#                 disc_amt = q2(sub * q2(payload.discount_pct) / Q("100"))
#             else:
#                 disc_amt = Q("0.00")
#             if disc_amt > sub:
#                 raise HTTPException(status_code=400, detail="discount exceeds sub_total")
#
#             taxable = q2(sub - disc_amt)
#
#             # tax
#             if payload.tax_pct is not None:
#                 tax_amt = q2(taxable * q2(payload.tax_pct) / Q("100"))
#             else:
#                 tax_amt = Q("0.00")
#
#             inv.discount_pct = payload.discount_pct
#             inv.discount_amount = disc_amt
#             inv.tax_pct = payload.tax_pct
#             inv.tax_amount = tax_amt
#             inv.grand_total = q2(taxable + tax_amt)
#             inv.status = "issued"
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def create_receipt(self, invoice_id: int, payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot receipt a void invoice")
#
#             amt = q2(payload.amount_received)
#             if amt <= 0:
#                 raise HTTPException(status_code=400, detail="amount_received must be > 0")
#
#             cash_total = Q("0.00")
#             utr_no = None
#
#             if payload.mode == "Cash":
#                 ensure_non_negative(
#                     payload.cash_500, payload.cash_200, payload.cash_100,
#                     payload.cash_50, payload.cash_20, payload.cash_10
#                 )
#                 cash_sum = sum_cash(
#                     payload.cash_500, payload.cash_200, payload.cash_100,
#                     payload.cash_50, payload.cash_20, payload.cash_10
#                 )
#                 if cash_sum <= 0:
#                     raise HTTPException(status_code=400, detail="Provide cash denominations for cash payment")
#                 cash_total = q2(cash_sum)
#                 if cash_total != amt:
#                     raise HTTPException(status_code=400, detail=f"Cash total ({cash_total}) does not match amount_received ({amt})")
#
#             else:
#                 utr_no = (payload.utr_no or "").strip()
#                 if not utr_no:
#                     raise HTTPException(status_code=400, detail="utr_no is required for non-cash payment")
#
#             rcpt = Receipt(
#                 invoice_id=invoice_id,
#                 amount_received=amt,
#                 mode=payload.mode,
#                 utr_no=utr_no if payload.mode != "Cash" else None,
#                 cash_500=int(payload.cash_500 or 0),
#                 cash_200=int(payload.cash_200 or 0),
#                 cash_100=int(payload.cash_100 or 0),
#                 cash_50=int(payload.cash_50 or 0),
#                 cash_20=int(payload.cash_20 or 0),
#                 cash_10=int(payload.cash_10 or 0),
#                 cash_total=cash_total if payload.mode == "Cash" else Q("0.00"),
#                 received_at=datetime.utcnow(),
#             )
#             db.add(rcpt)
#
#             inv.amount_paid = q2(Q(inv.amount_paid) + amt)
#             db.commit()
#             db.refresh(rcpt)
#             db.refresh(inv)
#
#             return rcpt, inv
#
#     def get_invoice(self, invoice_id: int) -> dict:
#         from app.models.people import Patient, Staff, Doctor
#         with SessionLocal() as db:
#             inv = (
#                 db.query(Invoice)
#                 .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
#                 .filter(Invoice.id == invoice_id)
#                 .first()
#             )
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#
#             # patient name
#             p = db.get(Patient, inv.patient_id)
#             patient_name = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"
#
#             return {
#                 "id": inv.id,
#                 "invoice_no": inv.invoice_no,
#                 "status": inv.status,
#                 "patient_name": patient_name,
#                 "visit_id": inv.visit_id,
#                 "appointment_id": inv.appointment_id,
#                 "sub_total": inv.sub_total,
#                 "discount_pct": inv.discount_pct,
#                 "discount_amount": inv.discount_amount,
#                 "tax_pct": inv.tax_pct,
#                 "tax_amount": inv.tax_amount,
#                 "grand_total": inv.grand_total,
#                 "amount_paid": inv.amount_paid,
#                 "created_at": inv.created_at,
#                 "items": inv.items,
#             }
#
#     def list_invoices(self, patient_id: int | None, date_from: datetime | None, date_to: datetime | None,
#                       status: str | None, page: int, page_size: int):
#         from app.models.people import Patient
#         from sqlalchemy import and_
#         with SessionLocal() as db:
#             base = select(Invoice, Patient.first_name, Patient.last_name).join(Patient, Patient.id == Invoice.patient_id)
#             if patient_id:
#                 base = base.where(Invoice.patient_id == patient_id)
#             if status:
#                 base = base.where(Invoice.status == status)
#             if date_from and date_to:
#                 base = base.where(and_(Invoice.created_at >= date_from, Invoice.created_at <= date_to))
#             elif date_from:
#                 base = base.where(Invoice.created_at >= date_from)
#             elif date_to:
#                 base = base.where(Invoice.created_at <= date_to)
#
#             total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
#             rows = db.execute(
#                 base.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
#             ).all()
#
#             items = []
#             for inv, pfn, pln in rows:
#                 items.append(
#                     {
#                         "id": inv.id,
#                         "invoice_no": inv.invoice_no,
#                         "patient_name": f"{pfn} {pln}".strip(),
#                         "status": inv.status,
#                         "grand_total": inv.grand_total,
#                         "amount_paid": inv.amount_paid,
#                         "created_at": inv.created_at,
#                     }
#                 )
#             return items, total

#
# from datetime import datetime
# from decimal import Decimal, ROUND_HALF_UP
# from fastapi import HTTPException
# from sqlalchemy import select, func
# from sqlalchemy.orm import joinedload
#
# from app.db.session import SessionLocal
# from app.models.billing import Invoice, InvoiceItem, Receipt
# from app.models.people import Patient, Staff, Doctor
# from app.models.opd import OPDVisit, OpdVisitLabTest
# from app.models.appointments import Appointment
# from app.utils.cash import ensure_non_negative, sum_cash
#
#
# Q = Decimal  # alias for readability
#
#
# def q2(v: Decimal | float | int) -> Decimal:
#     return Q(v).quantize(Q("0.01"), rounding=ROUND_HALF_UP)
#
#
# class BillingService:
#     def _gen_invoice_no(self, created_at: datetime, inv_id: int) -> str:
#         return f"INV{created_at:%y%m}{inv_id:05d}"
#
#     # --- simple pricing stub; plug your own price list here ---
#     def _lab_price(self, code: str | None, name: str) -> Decimal:
#         """
#         Return price for a lab test. Replace this with real pricing.
#         """
#         # Example hard-coded map by code; fallback 0
#         PRICE_BY_CODE = {
#             "CBC": Q("350.00"),
#             "LFT": Q("600.00"),
#             "KFT": Q("550.00"),
#         }
#         if code and code.strip() in PRICE_BY_CODE:
#             return PRICE_BY_CODE[code.strip()]
#         return Q("0.00")
#
#     def create_invoice(self, payload):
#         with SessionLocal() as db:
#             # resolve patient by id or patient_uid
#             patient_id = payload.patient_id
#             if not patient_id and getattr(payload, "patient_uid", None):
#                 patient_id = db.execute(
#                     select(Patient.id).where(Patient.patient_uid == payload.patient_uid.strip())
#                 ).scalar_one_or_none()
#             if not patient_id:
#                 raise HTTPException(status_code=400, detail="Provide valid patient_id or patient_uid")
#
#             # Optional links
#             visit_id = payload.visit_id
#             visit: OPDVisit | None = None
#             if visit_id:
#                 visit = db.get(OPDVisit, visit_id)
#                 if not visit:
#                     raise HTTPException(status_code=400, detail="visit_id not found")
#
#             appointment_id = payload.appointment_id
#             if appointment_id and not db.get(Appointment, appointment_id):
#                 raise HTTPException(status_code=400, detail="appointment_id not found")
#
#             inv = Invoice(
#                 patient_id=patient_id,
#                 visit_id=visit_id,
#                 appointment_id=appointment_id,
#                 status="draft",
#                 created_at=datetime.utcnow(),
#             )
#             db.add(inv)
#             db.flush()  # get inv.id
#
#             sub_total = Q("0.00")
#
#             # --- AUTO ITEMS FROM VISIT (if visit_id was provided) ---
#             payload_items = list(payload.items or [])
#             payload_has_consultation = any((it.item_type or "").lower() == "consultation" for it in payload_items)
#             payload_lab_ref_ids = {
#                 it.ref_id for it in payload_items if (it.item_type or "").lower() == "lab" and it.ref_id
#             }
#
#             if visit:
#                 # consultation fee from doctor (skip if client already sent a consultation item)
#                 if not payload_has_consultation:
#                     doc = db.get(Doctor, visit.doctor_id) if visit.doctor_id else None
#                     staff = db.get(Staff, doc.staff_id) if doc and doc.staff_id else None
#                     consultation_fee = q2(doc.consultation_fee or 0) if doc else Q("0.00")
#                     if consultation_fee > 0:
#                         desc = (
#                             f"Consultation - {staff.first_name} {staff.last_name}".strip()
#                             if staff else "Consultation"
#                         )
#                         line = consultation_fee  # qty=1
#                         db.add(
#                             InvoiceItem(
#                                 invoice_id=inv.id,
#                                 item_type="consultation",
#                                 ref_id=visit.doctor_id,
#                                 description=desc,
#                                 qty=1,
#                                 unit_price=consultation_fee,
#                                 line_total=line,
#                             )
#                         )
#                         sub_total += line
#
#                 # lab tests prescribed on this visit (status 'prescribed' or 'ordered')
#                 tests = db.execute(
#                     select(OpdVisitLabTest).where(
#                         OpdVisitLabTest.visit_id == visit.id,
#                         OpdVisitLabTest.status.in_(["prescribed", "ordered"])
#                     ).order_by(OpdVisitLabTest.id.asc())
#                 ).scalars().all()
#
#                 for t in tests:
#                     # avoid duplicate if caller already passed same ref_id lab line
#                     if t.id in payload_lab_ref_ids:
#                         continue
#                     price = q2(self._lab_price(t.test_code, t.test_name))
#                     line = price  # qty=1
#                     db.add(
#                         InvoiceItem(
#                             invoice_id=inv.id,
#                             item_type="lab",
#                             ref_id=t.id,
#                             description=t.test_name,
#                             qty=1,
#                             unit_price=price,
#                             line_total=line,
#                         )
#                     )
#                     sub_total += line
#
#             # --- CLIENT-PROVIDED ITEMS (if any) ---
#             for it in payload_items:
#                 qty = it.qty or 1
#                 unit = q2(it.unit_price or Q("0.00"))
#                 line = q2(Q(qty) * unit)
#                 db.add(
#                     InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type=it.item_type,
#                         ref_id=it.ref_id,
#                         description=it.description,
#                         qty=qty,
#                         unit_price=unit,
#                         line_total=line,
#                     )
#                 )
#                 sub_total += line
#
#             inv.sub_total = q2(sub_total)
#             db.flush()
#
#             # generate invoice_no
#             inv.invoice_no = self._gen_invoice_no(inv.created_at, inv.id)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def add_item(self, invoice_id: int, item_payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot add items to a void invoice")
#
#             qty = item_payload.qty or 1
#             unit = q2(item_payload.unit_price or Q("0.00"))
#             line = q2(Q(qty) * unit)
#             db.add(
#                 InvoiceItem(
#                     invoice_id=invoice_id,
#                     item_type=item_payload.item_type,
#                     ref_id=item_payload.ref_id,
#                     description=item_payload.description,
#                     qty=qty,
#                     unit_price=unit,
#                     line_total=line,
#                 )
#             )
#             inv.sub_total = q2(Q(inv.sub_total) + line)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def finalize(self, invoice_id: int, payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot finalize a void invoice")
#
#             sub = q2(inv.sub_total)
#             # discount
#             if payload.discount_amount is not None:
#                 disc_amt = q2(payload.discount_amount)
#             elif payload.discount_pct is not None:
#                 disc_amt = q2(sub * q2(payload.discount_pct) / Q("100"))
#             else:
#                 disc_amt = Q("0.00")
#             if disc_amt > sub:
#                 raise HTTPException(status_code=400, detail="discount exceeds sub_total")
#
#             taxable = q2(sub - disc_amt)
#
#             # tax
#             if payload.tax_pct is not None:
#                 tax_amt = q2(taxable * q2(payload.tax_pct) / Q("100"))
#             else:
#                 tax_amt = Q("0.00")
#
#             inv.discount_pct = payload.discount_pct
#             inv.discount_amount = disc_amt
#             inv.tax_pct = payload.tax_pct
#             inv.tax_amount = tax_amt
#             inv.grand_total = q2(taxable + tax_amt)
#             inv.status = "issued"
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def create_receipt(self, invoice_id: int, payload):
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status == "void":
#                 raise HTTPException(status_code=400, detail="Cannot receipt a void invoice")
#
#             amt = q2(payload.amount_received)
#             if amt <= 0:
#                 raise HTTPException(status_code=400, detail="amount_received must be > 0")
#
#             cash_total = Q("0.00")
#             utr_no = None
#
#             if payload.mode == "Cash":
#                 ensure_non_negative(
#                     payload.cash_500, payload.cash_200, payload.cash_100,
#                     payload.cash_50, payload.cash_20, payload.cash_10
#                 )
#                 cash_sum = sum_cash(
#                     payload.cash_500, payload.cash_200, payload.cash_100,
#                     payload.cash_50, payload.cash_20, payload.cash_10
#                 )
#                 if cash_sum <= 0:
#                     raise HTTPException(status_code=400, detail="Provide cash denominations for cash payment")
#                 cash_total = q2(cash_sum)
#                 if cash_total != amt:
#                     raise HTTPException(status_code=400, detail=f"Cash total ({cash_total}) does not match amount_received ({amt})")
#
#             else:
#                 utr_no = (payload.utr_no or "").strip()
#                 if not utr_no:
#                     raise HTTPException(status_code=400, detail="utr_no is required for non-cash payment")
#
#             rcpt = Receipt(
#                 invoice_id=invoice_id,
#                 amount_received=amt,
#                 mode=payload.mode,
#                 utr_no=utr_no if payload.mode != "Cash" else None,
#                 cash_500=int(payload.cash_500 or 0),
#                 cash_200=int(payload.cash_200 or 0),
#                 cash_100=int(payload.cash_100 or 0),
#                 cash_50=int(payload.cash_50 or 0),
#                 cash_20=int(payload.cash_20 or 0),
#                 cash_10=int(payload.cash_10 or 0),
#                 cash_total=cash_total if payload.mode == "Cash" else Q("0.00"),
#                 received_at=datetime.utcnow(),
#             )
#             db.add(rcpt)
#
#             inv.amount_paid = q2(Q(inv.amount_paid) + amt)
#             db.commit()
#             db.refresh(rcpt)
#             db.refresh(inv)
#
#             return rcpt, inv
#
#     def get_invoice(self, invoice_id: int) -> dict:
#         with SessionLocal() as db:
#             inv = (
#                 db.query(Invoice)
#                 .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
#                 .filter(Invoice.id == invoice_id)
#                 .first()
#             )
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#
#             # patient name
#             p = db.get(Patient, inv.patient_id)
#             patient_name = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"
#
#             return {
#                 "id": inv.id,
#                 "invoice_no": inv.invoice_no,
#                 "status": inv.status,
#                 "patient_name": patient_name,
#                 "visit_id": inv.visit_id,
#                 "appointment_id": inv.appointment_id,
#                 "sub_total": inv.sub_total,
#                 "discount_pct": inv.discount_pct,
#                 "discount_amount": inv.discount_amount,
#                 "tax_pct": inv.tax_pct,
#                 "tax_amount": inv.tax_amount,
#                 "grand_total": inv.grand_total,
#                 "amount_paid": inv.amount_paid,
#                 "created_at": inv.created_at,
#                 "items": inv.items,
#             }
#
#     def list_invoices(self, patient_id: int | None, date_from: datetime | None, date_to: datetime | None,
#                       status: str | None, page: int, page_size: int):
#         with SessionLocal() as db:
#             base = select(Invoice, Patient.first_name, Patient.last_name).join(Patient, Patient.id == Invoice.patient_id)
#             if patient_id:
#                 base = base.where(Invoice.patient_id == patient_id)
#             if status:
#                 base = base.where(Invoice.status == status)
#             if date_from and date_to:
#                 base = base.where(Invoice.created_at.between(date_from, date_to))
#             elif date_from:
#                 base = base.where(Invoice.created_at >= date_from)
#             elif date_to:
#                 base = base.where(Invoice.created_at <= date_to)
#
#             total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
#             rows = db.execute(
#                 base.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
#             ).all()
#
#             items = []
#             for inv, pfn, pln in rows:
#                 items.append(
#                     {
#                         "id": inv.id,
#                         "invoice_no": inv.invoice_no,
#                         "patient_name": f"{pfn} {pln}".strip(),
#                         "status": inv.status,
#                         "grand_total": inv.grand_total,
#                         "amount_paid": inv.amount_paid,
#                         "created_at": inv.created_at,
#                     }
#                 )
#             return items, total

#
# from __future__ import annotations
#
# from datetime import datetime
# from decimal import Decimal, ROUND_HALF_UP
# from sqlalchemy import select, func
# from sqlalchemy.orm import joinedload
#
# from app.db.session import SessionLocal
# from app.models.billing import Invoice, InvoiceItem, Receipt
# from app.models.people import Patient, Doctor, Staff
# from app.models.opd import OPDVisit, OpdVisitLabTest
# import os
# import pdfkit
# from jinja2 import Environment, FileSystemLoader, select_autoescape
# from fastapi import HTTPException
# from app.core.settings import settings
# # from app.utils.money import to_decimal  # create tiny helper or inline (see bottom)
#
# # tiny fallback if you don't have app/utils/money.py
# def to_decimal(val) -> Decimal:
#     try:
#         return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#     except Exception:
#         return Decimal("0.00")
#
# def _sum_cash(denoms: dict[str, int]) -> Decimal:
#     total = (
#         denoms.get("cash_500", 0) * 500
#         + denoms.get("cash_200", 0) * 200
#         + denoms.get("cash_100", 0) * 100
#         + denoms.get("cash_50", 0) * 50
#         + denoms.get("cash_20", 0) * 20
#         + denoms.get("cash_10", 0) * 10
#     )
#     return Decimal(total)
#
#
# class BillingService:
#     def _gen_invoice_no(self, inv: Invoice) -> str:
#         return f"INV{inv.created_at:%y%m}{inv.id:05d}"
#
#     # ---------- CREATE ----------
#     def create_invoice(self, payload) -> Invoice:
#         with SessionLocal() as db:
#             patient: Patient | None = None
#             if payload.patient_id:
#                 patient = db.get(Patient, payload.patient_id)
#             elif payload.patient_uid:
#                 patient = db.execute(select(Patient).where(Patient.patient_uid == payload.patient_uid)).scalar_one_or_none()
#             if not patient:
#                 raise HTTPException(status_code=400, detail="Patient not found")
#
#             visit: OPDVisit | None = None
#             if payload.visit_id:
#                 visit = db.get(OPDVisit, payload.visit_id)
#                 if not visit:
#                     raise HTTPException(status_code=400, detail="visit_id not found")
#                 if visit.patient_id != patient.id:
#                     raise HTTPException(status_code=400, detail="visit_id does not belong to patient")
#
#             inv = Invoice(
#                 patient_id=patient.id,
#                 visit_id=payload.visit_id,
#                 appointment_id=payload.appointment_id,
#                 status="draft",
#             )
#             db.add(inv)
#             db.flush()
#             inv.invoice_no = self._gen_invoice_no(inv)
#
#             # auto-add from visit
#             auto_total = Decimal("0.00")
#             if visit:
#                 # consultation fee
#                 doc = db.get(Doctor, visit.doctor_id)
#                 if doc and doc.consultation_fee:
#                     # get doctor name for description
#                     dname = db.execute(
#                         select(Staff.first_name, Staff.last_name).where(Staff.id == doc.staff_id)
#                     ).first()
#                     desc = f"Consultation - { (dname[0] or '') + ' ' + (dname[1] or '') if dname else 'Doctor' }".strip()
#                     fee = to_decimal(doc.consultation_fee)
#                     item = InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type="consultation",
#                         ref_id=doc.id,
#                         description=desc,
#                         qty=1,
#                         unit_price=fee,
#                         line_total=fee,
#                     )
#                     auto_total += fee
#                     db.add(item)
#
#                 # lab tests from visit (default price 0 unless overridden by manual item)
#                 tests: list[OpdVisitLabTest] = db.execute(
#                     select(OpdVisitLabTest).where(OpdVisitLabTest.visit_id == visit.id)
#                 ).scalars().all()
#
#                 # if user provided manual items with same ref_id, skip duplicates
#                 provided_ref_ids = {i.ref_id for i in (payload.items or []) if i.item_type == "lab" and i.ref_id}
#
#                 for t in tests:
#                     if t.id in provided_ref_ids:
#                         continue
#                     desc = f"Lab: {t.test_name}"
#                     price = Decimal("0.00")
#                     db.add(
#                         InvoiceItem(
#                             invoice_id=inv.id,
#                             item_type="lab",
#                             ref_id=t.id,
#                             description=desc,
#                             qty=1,
#                             unit_price=price,
#                             line_total=price,
#                         )
#                     )
#
#             # manual items
#             for it in payload.items or []:
#                 qty = int(it.qty or 1)
#                 unit = to_decimal(it.unit_price or 0)
#                 line = (unit * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#                 db.add(
#                     InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type=it.item_type,
#                         ref_id=it.ref_id,
#                         description=it.description,
#                         qty=qty,
#                         unit_price=unit,
#                         line_total=line,
#                     )
#                 )
#
#             # compute sub_total
#             sub_total = db.execute(
#                 select(func.coalesce(func.sum(InvoiceItem.line_total), 0))
#                 .where(InvoiceItem.invoice_id == inv.id)
#             ).scalar()
#             inv.sub_total = to_decimal(sub_total or 0)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     # ---------- ADD ITEM ----------
#     def add_item(self, invoice_id: int, it) -> Invoice:
#         with SessionLocal() as db:
#             inv = db.execute(
#                 select(Invoice).options(joinedload(Invoice.items)).where(Invoice.id == invoice_id)
#             ).scalar_one_or_none()
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status not in ("draft", "issued", "partially_paid"):
#                 raise HTTPException(status_code=400, detail="Cannot add items to this invoice")
#
#             qty = int(it.qty or 1)
#             unit = to_decimal(it.unit_price or 0)
#             line = (unit * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#
#             db.add(
#                 InvoiceItem(
#                     invoice_id=inv.id,
#                     item_type=it.item_type,
#                     ref_id=it.ref_id,
#                     description=it.description,
#                     qty=qty,
#                     unit_price=unit,
#                     line_total=line,
#                 )
#             )
#             inv.sub_total = (inv.sub_total + line).quantize(Decimal("0.01"))
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     # ---------- FINALIZE ----------
#     def finalize(self, invoice_id: int, disc_pct: float | None, disc_amt: float | None, tax_pct: float | None) -> Invoice:
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#
#             if disc_pct and disc_amt:
#                 raise HTTPException(status_code=400, detail="Use either discount_pct or discount_amount")
#
#             # fresh subtotal from items
#             sub_total = db.execute(
#                 select(func.coalesce(func.sum(InvoiceItem.line_total), 0))
#                 .where(InvoiceItem.invoice_id == inv.id)
#             ).scalar()
#             inv.sub_total = to_decimal(sub_total or 0)
#
#             discount_amount = Decimal("0.00")
#             if disc_pct is not None:
#                 inv.discount_pct = to_decimal(disc_pct)
#                 discount_amount = (inv.sub_total * inv.discount_pct / Decimal("100")).quantize(Decimal("0.01"))
#             elif disc_amt is not None:
#                 inv.discount_pct = None
#                 discount_amount = to_decimal(disc_amt)
#             inv.discount_amount = discount_amount
#
#             taxable = (inv.sub_total - discount_amount).quantize(Decimal("0.01"))
#             if taxable < 0:
#                 taxable = Decimal("0.00")
#
#             inv.tax_pct = to_decimal(tax_pct) if tax_pct is not None else None
#             tax_amount = Decimal("0.00")
#             if inv.tax_pct:
#                 tax_amount = (taxable * inv.tax_pct / Decimal("100")).quantize(Decimal("0.01"))
#             inv.tax_amount = tax_amount
#
#             inv.grand_total = (taxable + tax_amount).quantize(Decimal("0.01"))
#
#             # status transition
#             if inv.amount_paid >= inv.grand_total:
#                 inv.status = "paid"
#             else:
#                 inv.status = "issued"
#
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     # ---------- GET ----------
#     def get_invoice(self, invoice_id: int) -> dict:
#         with SessionLocal() as db:
#             inv = db.execute(
#                 select(Invoice)
#                 .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
#                 .where(Invoice.id == invoice_id)
#             ).scalar_one_or_none()
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#
#             # patient name
#             p = db.get(Patient, inv.patient_id)
#             pname = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"
#
#             return {
#                 "id": inv.id,
#                 "invoice_no": inv.invoice_no,
#                 "status": inv.status,
#                 "patient_id": inv.patient_id,
#                 "patient_name": pname,
#                 "visit_id": inv.visit_id,
#                 "appointment_id": inv.appointment_id,
#                 "sub_total": float(inv.sub_total or 0),
#                 "discount_pct": float(inv.discount_pct) if inv.discount_pct is not None else None,
#                 "discount_amount": float(inv.discount_amount or 0),
#                 "tax_pct": float(inv.tax_pct) if inv.tax_pct is not None else None,
#                 "tax_amount": float(inv.tax_amount or 0),
#                 "grand_total": float(inv.grand_total or 0),
#                 "amount_paid": float(inv.amount_paid or 0),
#                 "created_at": inv.created_at,
#                 "items": [
#                     {
#                         "id": it.id,
#                         "item_type": it.item_type,
#                         "ref_id": it.ref_id,
#                         "description": it.description,
#                         "qty": it.qty,
#                         "unit_price": float(it.unit_price or 0),
#                         "line_total": float(it.line_total or 0),
#                     }
#                     for it in inv.items
#                 ],
#             }
#
#     # ---------- LIST ----------
#     def list_invoices(self, patient_id: int | None, date_from: datetime | None, date_to: datetime | None,
#                       status: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
#         from app.models.people import Patient  # local import to avoid circulars
#         with SessionLocal() as db:
#             base = (
#                 select(
#                     Invoice,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                 )
#                 .join(Patient, Patient.id == Invoice.patient_id)
#             )
#             if patient_id:
#                 base = base.where(Invoice.patient_id == patient_id)
#             if status:
#                 base = base.where(Invoice.status == status)
#             if date_from and date_to:
#                 base = base.where(Invoice.created_at.between(date_from, date_to))
#             elif date_from:
#                 base = base.where(Invoice.created_at >= date_from)
#             elif date_to:
#                 base = base.where(Invoice.created_at <= date_to)
#
#             total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
#
#             rows = db.execute(
#                 base.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
#             ).all()
#
#             items: list[dict] = []
#             for row in rows:
#                 inv: Invoice = row[0]
#                 pname = f"{row.p_fn} {row.p_ln}".strip()
#                 items.append(
#                     {
#                         "id": inv.id,
#                         "invoice_no": inv.invoice_no,
#                         "status": inv.status,
#                         "patient_name": pname,
#                         "grand_total": float(inv.grand_total or 0),
#                         "amount_paid": float(inv.amount_paid or 0),
#                         "created_at": inv.created_at,
#                     }
#                 )
#             return items, total
#
#     # ---------- RECEIPT ----------
#     def create_receipt(self, invoice_id: int, payload) -> Receipt:
#         with SessionLocal() as db:
#             inv = db.get(Invoice, invoice_id)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             amt = to_decimal(payload.amount_received)
#
#             cash_total = Decimal("0.00")
#             utr = None
#
#             if payload.mode == "Cash":
#                 den = {
#                     "cash_500": payload.cash_500 or 0,
#                     "cash_200": payload.cash_200 or 0,
#                     "cash_100": payload.cash_100 or 0,
#                     "cash_50": payload.cash_50 or 0,
#                     "cash_20": payload.cash_20 or 0,
#                     "cash_10": payload.cash_10 or 0,
#                 }
#                 for k, v in den.items():
#                     if v < 0:
#                         raise HTTPException(status_code=400, detail=f"{k} cannot be negative")
#                 cash_total = _sum_cash(den)
#                 if cash_total != amt:
#                     raise HTTPException(status_code=400, detail=f"Cash denominations total {cash_total} != amount_received {amt}")
#             else:
#                 utr = (payload.utr_no or "").strip()
#                 if not utr:
#                     raise HTTPException(status_code=400, detail="utr_no is required for UPI/Card")
#
#             rcpt = Receipt(
#                 invoice_id=inv.id,
#                 amount_received=amt,
#                 mode=payload.mode,
#                 utr_no=utr,
#                 cash_500=payload.cash_500 or 0,
#                 cash_200=payload.cash_200 or 0,
#                 cash_100=payload.cash_100 or 0,
#                 cash_50=payload.cash_50 or 0,
#                 cash_20=payload.cash_20 or 0,
#                 cash_10=payload.cash_10 or 0,
#                 cash_total=cash_total,
#                 notes=payload.notes,
#             )
#             db.add(rcpt)
#
#             inv.amount_paid = (inv.amount_paid + amt).quantize(Decimal("0.01"))
#             if inv.amount_paid >= (inv.grand_total or Decimal("0.00")):
#                 inv.status = "paid"
#             elif inv.status in ("draft", "issued"):
#                 inv.status = "partially_paid"
#
#             db.commit()
#             db.refresh(rcpt)
#             return rcpt
#
#
#
#
#
#
# # append this inside BillingService
#
# def get_invoice_print_data(self, invoice_id: int) -> dict:
#     from app.models.people import Patient, Doctor, Staff
#     from app.models.opd import OPDVisit
#     from decimal import Decimal
#
#     with SessionLocal() as db:
#         inv = db.execute(
#             select(Invoice)
#             .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
#             .where(Invoice.id == invoice_id)
#         ).scalar_one_or_none()
#         if not inv:
#             raise HTTPException(status_code=404, detail="Invoice not found")
#
#         p = db.get(Patient, inv.patient_id)
#         patient_name = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"
#         patient_uid = getattr(p, "patient_uid", None)
#
#         visit_no = None
#         doctor_name = None
#         if inv.visit_id:
#             v = db.get(OPDVisit, inv.visit_id)
#             if v:
#                 visit_no = v.visit_no
#                 doc = db.get(Doctor, v.doctor_id)
#                 if doc:
#                     st = db.get(Staff, doc.staff_id)
#                     doctor_name = f"{(st.first_name or '')} {(st.last_name or '')}".strip() if st else None
#
#         sub_total = inv.sub_total or Decimal("0.00")
#         discount_amount = inv.discount_amount or Decimal("0.00")
#         tax_amount = inv.tax_amount or Decimal("0.00")
#         grand_total = inv.grand_total or Decimal("0.00")
#         amount_paid = inv.amount_paid or Decimal("0.00")
#         balance_due = (grand_total - amount_paid)
#
#         return {
#             "invoice_id": inv.id,
#             "invoice_no": inv.invoice_no,
#             "status": inv.status,
#             "created_at": inv.created_at,
#             "patient_name": patient_name,
#             "patient_uid": patient_uid,
#             "visit_no": visit_no,
#             "doctor_name": doctor_name,
#             "items": [
#                 {
#                     "description": it.description,
#                     "qty": it.qty,
#                     "unit_price": float(it.unit_price or 0),
#                     "line_total": float(it.line_total or 0),
#                     "item_type": it.item_type,
#                 }
#                 for it in inv.items
#             ],
#             "sub_total": float(sub_total),
#             "discount_pct": float(inv.discount_pct) if inv.discount_pct is not None else None,
#             "discount_amount": float(discount_amount),
#             "tax_pct": float(inv.tax_pct) if inv.tax_pct is not None else None,
#             "tax_amount": float(tax_amount),
#             "grand_total": float(grand_total),
#             "amount_paid": float(amount_paid),
#             "balance_due": float(balance_due),
#             "receipts": [
#                 {
#                     "amount": float(r.amount_received or 0),
#                     "mode": r.mode,
#                     "utr_no": r.utr_no,
#                     "received_at": r.received_at,
#                 }
#                 for r in inv.receipts
#             ],
#             "currency": "₹",  # adjust if needed
#             "hospital_name": "Your Hospital",  # plug org name here if you store it
#             "hospital_address": "",
#         }
#
#
#
# # inside class BillingService, add these methods
# def _render_invoice_html_for_pdf(self, data: dict) -> str:
#     env = Environment(
#         loader=FileSystemLoader("app/templates"),
#         autoescape=select_autoescape()
#     )
#     tpl = env.get_template("invoice_print.html")
#     static_fs = os.path.abspath("app/static").replace("\\", "/")
#     static_prefix = f"file:///{static_fs}"
#     return tpl.render(static_path=static_prefix, **data)
#
# def generate_invoice_pdf(self, invoice_id: int) -> str:
#     invoice, payload = self._load_invoice_with_lines(invoice_id)  # your existing helper
#     html_str = self._render_invoice_html(invoice, payload)        # your existing HTML renderer
#
#     out_dir = settings.PDF_OUTPUT_DIR
#     os.makedirs(out_dir, exist_ok=True)
#     out_path = os.path.join(out_dir, f"invoice_{invoice.invoice_no}.pdf")
#
#     config = None
#     if settings.WKHTMLTOPDF_CMD:
#         config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)
#
#     # allow images/fonts loaded from local file system if your HTML references them
#     options = {"enable-local-file-access": None}
#
#     pdfkit.from_string(html_str, out_path, configuration=config, options=options)
#     return out_path

#
#
# # app/services/billing.py
# from __future__ import annotations
# from datetime import datetime
# from decimal import Decimal, ROUND_HALF_UP
# from sqlalchemy import select, func
# from sqlalchemy.orm import joinedload, Session
# from fastapi import HTTPException
#
# from app.db.session import SessionLocal
# from app.models.billing import Invoice, InvoiceItem, Receipt
# from app.models.people import Patient, Doctor, Staff
# from app.models.opd import OPDVisit, OpdVisitLabTest
# from app.utils.tenant import Tenant
# from app.services._tenant_utils import _set_tenant_fields, _filter_by_tenant, _get_by_id_scoped
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import A4
# from pathlib import Path
#
# def to_decimal(val) -> Decimal:
#     try:
#         return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#     except Exception:
#         return Decimal("0.00")
#
# class BillingService:
#     def __init__(self, db: Session, tenant: Tenant) -> None:
#         self.db = db
#         self.tenant = tenant
#
#     def _gen_invoice_no(self, inv: Invoice) -> str:
#         return f"INV{inv.created_at:%y%m}{inv.id:05d}"
#
#     # ---------- CREATE ----------
#     def create_invoice(self, payload) -> Invoice:
#         with SessionLocal() as db:
#             # resolve patient within tenant
#             patient = None
#             if payload.patient_id:
#                 patient = _get_by_id_scoped(db, Patient, payload.patient_id, self.tenant)
#             elif getattr(payload, "patient_uid", None):
#                 stmt = select(Patient).where(Patient.patient_uid == payload.patient_uid.strip())
#                 stmt = _filter_by_tenant(stmt, Patient, self.tenant)
#                 patient = db.execute(stmt).scalar_one_or_none()
#             if not patient:
#                 raise HTTPException(status_code=400, detail="Patient not found")
#
#             visit = None
#             if payload.visit_id:
#                 visit = _get_by_id_scoped(db, OPDVisit, payload.visit_id, self.tenant)
#                 if not visit:
#                     raise HTTPException(status_code=400, detail="visit_id not found")
#                 if visit.patient_id != patient.id:
#                     raise HTTPException(status_code=400, detail="visit_id does not belong to patient")
#
#             if payload.appointment_id:
#                 # If you have Appointment model, scope-check here similarly (optional)
#                 pass
#
#             inv = Invoice(
#                 patient_id=patient.id,
#                 visit_id=payload.visit_id,
#                 appointment_id=payload.appointment_id,
#                 status="draft",
#             )
#             _set_tenant_fields(inv, self.tenant)
#             db.add(inv)
#             db.flush()
#             inv.invoice_no = self._gen_invoice_no(inv)
#
#             # auto-add from visit (consultation + lab)
#             if visit:
#                 doc = _get_by_id_scoped(db, Doctor, visit.doctor_id, self.tenant) if visit.doctor_id else None
#                 if doc and doc.consultation_fee:
#                     staff = _get_by_id_scoped(db, Staff, doc.staff_id, self.tenant) if doc.staff_id else None
#                     desc = f"Consultation - { (staff.first_name or '')} {(staff.last_name or '')}".strip() if staff else "Consultation"
#                     fee = to_decimal(doc.consultation_fee)
#                     item = InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type="consultation",
#                         ref_id=doc.id,
#                         description=desc,
#                         qty=1,
#                         unit_price=fee,
#                         line_total=fee,
#                     )
#                     _set_tenant_fields(item, self.tenant)
#                     db.add(item)
#
#                 provided_lab_ref_ids = {
#                     it.ref_id for it in (payload.items or [])
#                     if (getattr(it, "item_type", "") or "").lower() == "lab" and it.ref_id
#                 }
#                 lab_q = select(OpdVisitLabTest).where(OpdVisitLabTest.visit_id == visit.id)
#                 lab_q = _filter_by_tenant(lab_q, OpdVisitLabTest, self.tenant) if hasattr(OpdVisitLabTest, "branch_id") else lab_q
#                 tests = db.execute(lab_q).scalars().all()
#                 for t in tests:
#                     if t.id in provided_lab_ref_ids:
#                         continue
#                     it = InvoiceItem(
#                         invoice_id=inv.id,
#                         item_type="lab",
#                         ref_id=t.id,
#                         description=f"Lab: {t.test_name}",
#                         qty=1,
#                         unit_price=to_decimal(0),
#                         line_total=to_decimal(0),
#                     )
#                     _set_tenant_fields(it, self.tenant)
#                     db.add(it)
#
#             # manual items
#             for itp in payload.items or []:
#                 qty = int(itp.qty or 1)
#                 unit = to_decimal(itp.unit_price or 0)
#                 line = (unit * qty).quantize(Decimal("0.01"))
#                 it = InvoiceItem(
#                     invoice_id=inv.id,
#                     item_type=itp.item_type,
#                     ref_id=itp.ref_id,
#                     description=itp.description,
#                     qty=qty,
#                     unit_price=unit,
#                     line_total=line,
#                 )
#                 _set_tenant_fields(it, self.tenant)
#                 db.add(it)
#
#             # compute sub_total
#             sub_stmt = select(func.coalesce(func.sum(InvoiceItem.line_total), 0)).where(InvoiceItem.invoice_id == inv.id)
#             sub_stmt = _filter_by_tenant(sub_stmt, InvoiceItem, self.tenant) if hasattr(InvoiceItem, "branch_id") else sub_stmt
#             inv.sub_total = to_decimal(db.execute(sub_stmt).scalar() or 0)
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def add_item(self, invoice_id: int, itp) -> Invoice:
#         with SessionLocal() as db:
#             inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if inv.status not in ("draft", "issued", "partially_paid"):
#                 raise HTTPException(status_code=400, detail="Cannot add items to this invoice")
#
#             qty = int(itp.qty or 1)
#             unit = to_decimal(itp.unit_price or 0)
#             line = (unit * qty).quantize(Decimal("0.01"))
#             it = InvoiceItem(
#                 invoice_id=inv.id,
#                 item_type=itp.item_type,
#                 ref_id=itp.ref_id,
#                 description=itp.description,
#                 qty=qty,
#                 unit_price=unit,
#                 line_total=line,
#             )
#             _set_tenant_fields(it, self.tenant)
#             db.add(it)
#             inv.sub_total = (inv.sub_total + line).quantize(Decimal("0.01"))
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def finalize(self, invoice_id: int, disc_pct: float | None, disc_amt: float | None, tax_pct: float | None) -> Invoice:
#         with SessionLocal() as db:
#             inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             if disc_pct and disc_amt:
#                 raise HTTPException(status_code=400, detail="Use either discount_pct or discount_amount")
#
#             sub_stmt = select(func.coalesce(func.sum(InvoiceItem.line_total), 0)).where(InvoiceItem.invoice_id == inv.id)
#             sub_stmt = _filter_by_tenant(sub_stmt, InvoiceItem, self.tenant) if hasattr(InvoiceItem, "branch_id") else sub_stmt
#             inv.sub_total = to_decimal(db.execute(sub_stmt).scalar() or 0)
#
#             discount_amount = Decimal("0.00")
#             if disc_pct is not None:
#                 inv.discount_pct = to_decimal(disc_pct)
#                 discount_amount = (inv.sub_total * inv.discount_pct / Decimal("100")).quantize(Decimal("0.01"))
#             elif disc_amt is not None:
#                 inv.discount_pct = None
#                 discount_amount = to_decimal(disc_amt)
#             inv.discount_amount = discount_amount
#
#             taxable = (inv.sub_total - discount_amount)
#             if taxable < 0:
#                 taxable = Decimal("0.00")
#
#             inv.tax_pct = to_decimal(tax_pct) if tax_pct is not None else None
#             tax_amount = Decimal("0.00")
#             if inv.tax_pct:
#                 tax_amount = (taxable * inv.tax_pct / Decimal("100")).quantize(Decimal("0.01"))
#             inv.tax_amount = tax_amount
#             inv.grand_total = (taxable + tax_amount).quantize(Decimal("0.01"))
#
#             inv.status = "paid" if inv.amount_paid >= inv.grand_total else "issued"
#             db.commit()
#             db.refresh(inv)
#             return inv
#
#     def get_invoice(self, invoice_id: int) -> dict:
#         with SessionLocal() as db:
#             stmt = (
#                 select(Invoice)
#                 .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
#                 .where(Invoice.id == invoice_id)
#             )
#             stmt = _filter_by_tenant(stmt, Invoice, self.tenant)
#             # inv = db.execute(stmt).scalar_one_or_none()
#             inv = db.execute(stmt).unique().scalar_one_or_none()
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#
#             p = _get_by_id_scoped(db, Patient, inv.patient_id, self.tenant)
#             pname = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"
#
#             return {
#                 "id": inv.id,
#                 "invoice_no": inv.invoice_no,
#                 "status": inv.status,
#                 "patient_id": inv.patient_id,
#                 "patient_name": pname,
#                 "visit_id": inv.visit_id,
#                 "appointment_id": inv.appointment_id,
#                 "sub_total": float(inv.sub_total or 0),
#                 "discount_pct": float(inv.discount_pct) if inv.discount_pct is not None else None,
#                 "discount_amount": float(inv.discount_amount or 0),
#                 "tax_pct": float(inv.tax_pct) if inv.tax_pct is not None else None,
#                 "tax_amount": float(inv.tax_amount or 0),
#                 "grand_total": float(inv.grand_total or 0),
#                 "amount_paid": float(inv.amount_paid or 0),
#                 "created_at": inv.created_at,
#                 "items": [
#                     {
#                         "id": it.id,
#                         "item_type": it.item_type,
#                         "ref_id": it.ref_id,
#                         "description": it.description,
#                         "qty": it.qty,
#                         "unit_price": float(it.unit_price or 0),
#                         "line_total": float(it.line_total or 0),
#                     }
#                     for it in inv.items
#                 ],
#             }
#
#     def list_invoices(self, patient_id: int | None, date_from: datetime | None, date_to: datetime | None,
#                       status: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
#         with SessionLocal() as db:
#             base = (
#                 select(
#                     Invoice,
#                     Patient.first_name.label("p_fn"),
#                     Patient.last_name.label("p_ln"),
#                 )
#                 .join(Patient, Patient.id == Invoice.patient_id)
#             )
#             base = _filter_by_tenant(base, Invoice, self.tenant)
#             base = _filter_by_tenant(base, Patient, self.tenant)
#
#             if patient_id:
#                 base = base.where(Invoice.patient_id == patient_id)
#             if status:
#                 base = base.where(Invoice.status == status)
#             if date_from and date_to:
#                 base = base.where(Invoice.created_at.between(date_from, date_to))
#             elif date_from:
#                 base = base.where(Invoice.created_at >= date_from)
#             elif date_to:
#                 base = base.where(Invoice.created_at <= date_to)
#
#             total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
#             rows = db.execute(
#                 base.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
#             ).all()
#
#             items: list[dict] = []
#             for row in rows:
#                 inv: Invoice = row[0]
#                 pname = f"{row.p_fn} {row.p_ln}".strip()
#                 items.append(
#                     {
#                         "id": inv.id,
#                         "invoice_no": inv.invoice_no,
#                         "status": inv.status,
#                         "patient_name": pname,
#                         "grand_total": float(inv.grand_total or 0),
#                         "amount_paid": float(inv.amount_paid or 0),
#                         "created_at": inv.created_at,
#                     }
#                 )
#             return items, total
#
#     def create_receipt(self, invoice_id: int, payload) -> Receipt:
#         from decimal import Decimal
#         with SessionLocal() as db:
#             inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
#             if not inv:
#                 raise HTTPException(status_code=404, detail="Invoice not found")
#             amt = to_decimal(payload.amount_received)
#             if amt <= 0:
#                 raise HTTPException(status_code=400, detail="amount_received must be > 0")
#
#             cash_total = Decimal("0.00")
#             utr = None
#
#             if payload.mode == "Cash":
#                 denoms = {
#                     "cash_500": payload.cash_500 or 0,
#                     "cash_200": payload.cash_200 or 0,
#                     "cash_100": payload.cash_100 or 0,
#                     "cash_50": payload.cash_50 or 0,
#                     "cash_20": payload.cash_20 or 0,
#                     "cash_10": payload.cash_10 or 0,
#                 }
#                 for k, v in denoms.items():
#                     if v < 0:
#                         raise HTTPException(status_code=400, detail=f"{k} cannot be negative")
#                 cash_total = Decimal(
#                     denoms["cash_500"]*500 + denoms["cash_200"]*200 + denoms["cash_100"]*100 +
#                     denoms["cash_50"]*50 + denoms["cash_20"]*20 + denoms["cash_10"]*10
#                 )
#                 if cash_total != amt:
#                     raise HTTPException(status_code=400, detail=f"Cash denominations total {cash_total} != amount_received {amt}")
#             else:
#                 utr = (payload.utr_no or "").strip()
#                 if not utr:
#                     raise HTTPException(status_code=400, detail="utr_no is required for UPI/Card")
#
#             rcpt = Receipt(
#                 invoice_id=inv.id,
#                 amount_received=amt,
#                 mode=payload.mode,
#                 utr_no=utr,
#                 cash_500=payload.cash_500 or 0,
#                 cash_200=payload.cash_200 or 0,
#                 cash_100=payload.cash_100 or 0,
#                 cash_50=payload.cash_50 or 0,
#                 cash_20=payload.cash_20 or 0,
#                 cash_10=payload.cash_10 or 0,
#                 cash_total=cash_total,
#                 notes=payload.notes,
#             )
#             _set_tenant_fields(rcpt, self.tenant)
#             db.add(rcpt)
#
#             inv.amount_paid = (inv.amount_paid + amt).quantize(Decimal("0.01"))
#             inv.status = "paid" if inv.amount_paid >= (inv.grand_total or Decimal("0.00")) else ("partially_paid" if inv.status in ("draft","issued") else inv.status)
#
#             db.commit()
#             db.refresh(rcpt)
#             return rcpt
#
#     def generate_and_save_invoice_pdf(self, invoice_id: int, storage) -> tuple[str, str, str | None]:
#         # 1) fetch ORM invoice (tenant-scoped)
#         inv = _get_by_id_scoped(self.db, Invoice, invoice_id, self.tenant)
#         if not inv:
#             raise HTTPException(status_code=404, detail="Invoice not found")
#
#         # 2) fetch display data for PDF
#         inv_dict = self.get_invoice(invoice_id)  # returns dict with items etc.
#
#         # 3) render
#         filename = f"{inv_dict['invoice_no'] or 'INV'}-{invoice_id}.pdf"
#         rel_path = f"invoices/{filename}"
#
#         tmp = Path("static/_tmp")
#         tmp.mkdir(parents=True, exist_ok=True)
#         pdf_tmp = tmp / filename
#
#         c = canvas.Canvas(str(pdf_tmp), pagesize=A4)
#         c.drawString(40, 800, f"Invoice: {inv_dict['invoice_no']}")
#         c.drawString(40, 780, f"Patient: {inv_dict['patient_name']}")
#         c.drawString(40, 760, f"Total: {inv_dict['grand_total']}")
#         y = 730
#         for it in inv_dict["items"]:
#             c.drawString(40, y, f"- {it['description']}  x{it['qty']}  = {it['line_total']}")
#             y -= 16
#             if y < 60:
#                 c.showPage();
#                 y = 800
#         c.showPage();
#         c.save()
#
#         # 4) save via storage
#         abs_path = storage.save_bytes(rel_path, pdf_tmp.read_bytes())
#         url = storage.url_for(rel_path)  # LocalStorage will likely return None
#
#         # 5) PERSIST on the invoice so GET works later
#         inv.pdf_path = abs_path
#         inv.pdf_url = url
#         self.db.commit()
#         self.db.refresh(inv)
#
#         return abs_path, filename, url



# app/services/billing.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload, Session

from app.models.billing import Invoice, InvoiceItem, Receipt
from app.models.people import Patient, Doctor, Staff
from app.models.opd import OPDVisit, OpdVisitLabTest
from app.utils.tenant import Tenant
from app.services._tenant_utils import _filter_by_tenant, _get_by_id_scoped
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def to_decimal(val) -> Decimal:
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


class BillingService:
    def __init__(self, db: Session, tenant: Tenant) -> None:
        self.db = db
        self.tenant = tenant

    def _gen_invoice_no(self, inv: Invoice) -> str:
        return f"INV{inv.created_at:%y%m}{inv.id:05d}"

    # ---------- CREATE ----------
    def create_invoice(self, payload) -> Invoice:
        db = self.db

        # resolve patient within tenant (by id or patient_uid)
        patient = None
        if payload.patient_id:
            patient = _get_by_id_scoped(db, Patient, payload.patient_id, self.tenant)
        elif getattr(payload, "patient_uid", None):
            stmt = select(Patient).where(Patient.patient_uid == payload.patient_uid.strip())
            stmt = _filter_by_tenant(stmt, Patient, self.tenant)
            patient = db.execute(stmt).scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=400, detail="Patient not found")

        # optional visit check
        visit = None
        if payload.visit_id:
            visit = _get_by_id_scoped(db, OPDVisit, payload.visit_id, self.tenant)
            if not visit:
                raise HTTPException(status_code=400, detail="visit_id not found")
            if visit.patient_id != patient.id:
                raise HTTPException(status_code=400, detail="visit_id does not belong to patient")

        # create invoice WITH tenant fields explicitly
        inv = Invoice(
            patient_id=patient.id,
            visit_id=payload.visit_id,
            appointment_id=payload.appointment_id,
            status="draft",
            hospital_id=self.tenant.hospital_id,
            branch_id=self.tenant.branch_id,
        )
        db.add(inv)
        db.flush()  # inv.id
        inv.invoice_no = self._gen_invoice_no(inv)

        # auto items from visit (consultation + labs)
        if visit:
            doc = _get_by_id_scoped(db, Doctor, visit.doctor_id, self.tenant) if visit.doctor_id else None
            if doc and doc.consultation_fee:
                staff = _get_by_id_scoped(db, Staff, doc.staff_id, self.tenant) if doc.staff_id else None
                desc = f"Consultation - { (staff.first_name or '')} {(staff.last_name or '')}".strip() if staff else "Consultation"
                fee = to_decimal(doc.consultation_fee)
                db.add(InvoiceItem(
                    invoice_id=inv.id,
                    item_type="consultation",
                    ref_id=doc.id,
                    description=desc,
                    qty=1,
                    unit_price=fee,
                    line_total=fee,
                    hospital_id=self.tenant.hospital_id,
                    branch_id=self.tenant.branch_id,
                ))

            provided_lab_ref_ids = {
                it.ref_id for it in (payload.items or [])
                if (getattr(it, "item_type", "") or "").lower() == "lab" and it.ref_id
            }
            lab_q = select(OpdVisitLabTest).where(OpdVisitLabTest.visit_id == visit.id)
            lab_q = _filter_by_tenant(lab_q, OpdVisitLabTest, self.tenant) if hasattr(OpdVisitLabTest, "branch_id") else lab_q
            for t in db.execute(lab_q).scalars().all():
                if t.id in provided_lab_ref_ids:
                    continue
                db.add(InvoiceItem(
                    invoice_id=inv.id,
                    item_type="lab",
                    ref_id=t.id,
                    description=f"Lab: {t.test_name}",
                    qty=1,
                    unit_price=to_decimal(0),
                    line_total=to_decimal(0),
                    hospital_id=self.tenant.hospital_id,
                    branch_id=self.tenant.branch_id,
                ))

        # manual items
        for itp in payload.items or []:
            qty = int(itp.qty or 1)
            unit = to_decimal(itp.unit_price or 0)
            line = (unit * qty).quantize(Decimal("0.01"))
            db.add(InvoiceItem(
                invoice_id=inv.id,
                item_type=itp.item_type,
                ref_id=itp.ref_id,
                description=itp.description,
                qty=qty,
                unit_price=unit,
                line_total=line,
                hospital_id=self.tenant.hospital_id,
                branch_id=self.tenant.branch_id,
            ))

        # compute sub_total
        sub_stmt = select(func.coalesce(func.sum(InvoiceItem.line_total), 0)).where(InvoiceItem.invoice_id == inv.id)
        sub_stmt = _filter_by_tenant(sub_stmt, InvoiceItem, self.tenant) if hasattr(InvoiceItem, "branch_id") else sub_stmt
        inv.sub_total = to_decimal(db.execute(sub_stmt).scalar() or 0)

        db.commit()
        db.refresh(inv)
        return inv

    def add_item(self, invoice_id: int, itp) -> Invoice:
        db = self.db
        inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if inv.status not in ("draft", "issued", "partially_paid"):
            raise HTTPException(status_code=400, detail="Cannot add items to this invoice")

        qty = int(itp.qty or 1)
        unit = to_decimal(itp.unit_price or 0)
        line = (unit * qty).quantize(Decimal("0.01"))
        db.add(InvoiceItem(
            invoice_id=inv.id,
            item_type=itp.item_type,
            ref_id=itp.ref_id,
            description=itp.description,
            qty=qty,
            unit_price=unit,
            line_total=line,
            hospital_id=self.tenant.hospital_id,
            branch_id=self.tenant.branch_id,
        ))
        inv.sub_total = (inv.sub_total + line).quantize(Decimal("0.01"))

        db.commit()
        db.refresh(inv)
        return inv

    def finalize(self, invoice_id: int, disc_pct: float | None, disc_amt: float | None, tax_pct: float | None) -> Invoice:
        db = self.db
        inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if disc_pct and disc_amt:
            raise HTTPException(status_code=400, detail="Use either discount_pct or discount_amount")

        sub_stmt = select(func.coalesce(func.sum(InvoiceItem.line_total), 0)).where(InvoiceItem.invoice_id == inv.id)
        sub_stmt = _filter_by_tenant(sub_stmt, InvoiceItem, self.tenant) if hasattr(InvoiceItem, "branch_id") else sub_stmt
        inv.sub_total = to_decimal(db.execute(sub_stmt).scalar() or 0)

        discount_amount = Decimal("0.00")
        if disc_pct is not None:
            inv.discount_pct = to_decimal(disc_pct)
            discount_amount = (inv.sub_total * inv.discount_pct / Decimal("100")).quantize(Decimal("0.01"))
        elif disc_amt is not None:
            inv.discount_pct = None
            discount_amount = to_decimal(disc_amt)
        inv.discount_amount = discount_amount

        taxable = (inv.sub_total - discount_amount)
        if taxable < 0:
            taxable = Decimal("0.00")

        inv.tax_pct = to_decimal(tax_pct) if tax_pct is not None else None
        tax_amount = Decimal("0.00")
        if inv.tax_pct:
            tax_amount = (taxable * inv.tax_pct / Decimal("100")).quantize(Decimal("0.01"))
        inv.tax_amount = tax_amount
        inv.grand_total = (taxable + tax_amount).quantize(Decimal("0.01"))

        inv.status = "paid" if inv.amount_paid >= inv.grand_total else "issued"

        db.commit()
        db.refresh(inv)
        return inv

    def get_invoice(self, invoice_id: int) -> dict:
        db = self.db
        stmt = (
            select(Invoice)
            .options(joinedload(Invoice.items), joinedload(Invoice.receipts))
            .where(Invoice.id == invoice_id)
        )
        stmt = _filter_by_tenant(stmt, Invoice, self.tenant)
        inv = db.execute(stmt).unique().scalar_one_or_none()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")

        p = _get_by_id_scoped(db, Patient, inv.patient_id, self.tenant)
        pname = f"{p.first_name} {p.last_name}".strip() if p else "Unknown"

        return {
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "status": inv.status,
            "patient_id": inv.patient_id,
            "patient_name": pname,
            "visit_id": inv.visit_id,
            "appointment_id": inv.appointment_id,
            "sub_total": float(inv.sub_total or 0),
            "discount_pct": float(inv.discount_pct) if inv.discount_pct is not None else None,
            "discount_amount": float(inv.discount_amount or 0),
            "tax_pct": float(inv.tax_pct) if inv.tax_pct is not None else None,
            "tax_amount": float(inv.tax_amount or 0),
            "grand_total": float(inv.grand_total or 0),
            "amount_paid": float(inv.amount_paid or 0),
            "created_at": inv.created_at,
            "items": [
                {
                    "id": it.id,
                    "item_type": it.item_type,
                    "ref_id": it.ref_id,
                    "description": it.description,
                    "qty": it.qty,
                    "unit_price": float(it.unit_price or 0),
                    "line_total": float(it.line_total or 0),
                }
                for it in inv.items
            ],
        }

    def list_invoices(self, patient_id: int | None, date_from: datetime | None, date_to: datetime | None,
                      status: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
        db = self.db
        base = (
            select(
                Invoice,
                Patient.first_name.label("p_fn"),
                Patient.last_name.label("p_ln"),
            )
            .join(Patient, Patient.id == Invoice.patient_id)
        )
        base = _filter_by_tenant(base, Invoice, self.tenant)
        base = _filter_by_tenant(base, Patient, self.tenant)

        if patient_id:
            base = base.where(Invoice.patient_id == patient_id)
        if status:
            base = base.where(Invoice.status == status)
        if date_from and date_to:
            base = base.where(Invoice.created_at.between(date_from, date_to))
        elif date_from:
            base = base.where(Invoice.created_at >= date_from)
        elif date_to:
            base = base.where(Invoice.created_at <= date_to)

        total = int(db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0)
        rows = db.execute(
            base.order_by(Invoice.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()

        items: list[dict] = []
        for row in rows:
            inv: Invoice = row[0]
            pname = f"{row.p_fn} {row.p_ln}".strip()
            items.append(
                {
                    "id": inv.id,
                    "invoice_no": inv.invoice_no,
                    "status": inv.status,
                    "patient_name": pname,
                    "grand_total": float(inv.grand_total or 0),
                    "amount_paid": float(inv.amount_paid or 0),
                    "created_at": inv.created_at,
                }
            )
        return items, total

    def create_receipt(self, invoice_id: int, payload) -> Receipt:
        from decimal import Decimal
        db = self.db

        inv = _get_by_id_scoped(db, Invoice, invoice_id, self.tenant)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")

        amt = to_decimal(payload.amount_received)
        if amt <= 0:
            raise HTTPException(status_code=400, detail="amount_received must be > 0")

        cash_total = Decimal("0.00")
        utr = None

        if payload.mode == "Cash":
            denoms = {
                "cash_500": payload.cash_500 or 0,
                "cash_200": payload.cash_200 or 0,
                "cash_100": payload.cash_100 or 0,
                "cash_50": payload.cash_50 or 0,
                "cash_20": payload.cash_20 or 0,
                "cash_10": payload.cash_10 or 0,
            }
            for k, v in denoms.items():
                if v < 0:
                    raise HTTPException(status_code=400, detail=f"{k} cannot be negative")
            cash_total = Decimal(
                denoms["cash_500"]*500 + denoms["cash_200"]*200 + denoms["cash_100"]*100 +
                denoms["cash_50"]*50 + denoms["cash_20"]*20 + denoms["cash_10"]*10
            )
            if cash_total != amt:
                raise HTTPException(status_code=400, detail=f"Cash denominations total {cash_total} != amount_received {amt}")
        else:
            utr = (payload.utr_no or "").strip()
            if not utr:
                raise HTTPException(status_code=400, detail="utr_no is required for UPI/Card")

        rcpt = Receipt(
            invoice_id=inv.id,
            amount_received=amt,
            mode=payload.mode,
            utr_no=utr,
            cash_500=payload.cash_500 or 0,
            cash_200=payload.cash_200 or 0,
            cash_100=payload.cash_100 or 0,
            cash_50=payload.cash_50 or 0,
            cash_20=payload.cash_20 or 0,
            cash_10=payload.cash_10 or 0,
            cash_total=cash_total,
            notes=payload.notes,
            hospital_id=self.tenant.hospital_id,
            branch_id=self.tenant.branch_id,
        )
        db.add(rcpt)

        inv.amount_paid = (inv.amount_paid + amt).quantize(Decimal("0.01"))
        inv.status = "paid" if inv.amount_paid >= (inv.grand_total or Decimal("0.00")) else (
            "partially_paid" if inv.status in ("draft", "issued") else inv.status
        )

        db.commit()
        db.refresh(rcpt)
        return rcpt

    def generate_and_save_invoice_pdf(self, invoice_id: int, storage) -> tuple[str, str, str | None]:
        # fetch ORM invoice (tenant-scoped)
        inv = _get_by_id_scoped(self.db, Invoice, invoice_id, self.tenant)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # display data
        inv_dict = self.get_invoice(invoice_id)

        # render
        filename = f"{inv_dict['invoice_no'] or 'INV'}-{invoice_id}.pdf"
        rel_path = f"invoices/{filename}"

        tmp = Path("static/_tmp")
        tmp.mkdir(parents=True, exist_ok=True)
        pdf_tmp = tmp / filename

        c = canvas.Canvas(str(pdf_tmp), pagesize=A4)
        c.drawString(40, 800, f"Invoice: {inv_dict['invoice_no']}")
        c.drawString(40, 780, f"Patient: {inv_dict['patient_name']}")
        c.drawString(40, 760, f"Total: {inv_dict['grand_total']}")
        y = 730
        for it in inv_dict["items"]:
            c.drawString(40, y, f"- {it['description']}  x{it['qty']}  = {it['line_total']}")
            y -= 16
            if y < 60:
                c.showPage(); y = 800
        c.showPage(); c.save()

        # save
        abs_path = storage.save_bytes(rel_path, pdf_tmp.read_bytes())
        url = storage.url_for(rel_path)  # None for LocalStorage

        # persist path/url for GET endpoint
        inv.pdf_path = abs_path
        inv.pdf_url = url
        self.db.commit()
        self.db.refresh(inv)

        return abs_path, filename, url
