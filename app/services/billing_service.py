# app/services/billing_service.py
from __future__ import annotations
from typing import Tuple
from pathlib import Path
from decimal import Decimal

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.models.billing import Invoice
from app.utils.storage import StorageBackend
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pathlib import Path

from app.utils.tenant import Tenant
from app.services.billing import BillingService  # import original

class BillingPDFService:
    def __init__(self, db: Session, storage: StorageBackend,tenant: Tenant,):
        self.db = db
        self.storage = storage
        self.tenant = tenant


    def _relative_pdf_path(self, invoice_id: int) -> str:
        return f"invoices/invoice_{invoice_id}.pdf"

    def _render_pdf(self, invoice: Invoice) -> bytes:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Invoice #{invoice.invoice_no or invoice.id}", ln=1)

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"Status: {invoice.status}", ln=1)
        pdf.cell(0, 7, f"Date: {invoice.created_at}", ln=1)
        pdf.cell(0, 7, f"Patient ID: {invoice.patient_id}", ln=1)
        if invoice.appointment_id:
            pdf.cell(0, 7, f"Appointment ID: {invoice.appointment_id}", ln=1)
        if invoice.visit_id:
            pdf.cell(0, 7, f"Visit ID: {invoice.visit_id}", ln=1)
        pdf.ln(5)

        # Table header
        pdf.set_font("Helvetica", "B", 11)
        col_w = [90, 18, 32, 40]  # Description, Qty, Unit Price, Line Total
        headers = ["Item", "Qty", "Rate", "Amount"]
        for text, w in zip(headers, col_w):
            pdf.cell(w, 8, text, border=1)
        pdf.ln(8)

        # Items
        pdf.set_font("Helvetica", "", 11)
        running_subtotal = Decimal("0.00")
        for it in (invoice.items or []):
            desc = (it.description or "")[:90] + ("…" if len((it.description or "")) > 90 else "")
            qty = it.qty or 0
            rate = it.unit_price or Decimal("0.00")
            line_total = it.line_total or (Decimal(qty) * rate)
            running_subtotal += line_total

            pdf.cell(col_w[0], 8, desc, border=1)
            pdf.cell(col_w[1], 8, f"{qty}", border=1, align="R")
            pdf.cell(col_w[2], 8, f"{rate:.2f}", border=1, align="R")
            pdf.cell(col_w[3], 8, f"{line_total:.2f}", border=1, align="R")
            pdf.ln(8)

        # Totals section (uses your invoice fields if present; otherwise computed)
        pdf.ln(2)
        def rcell(label: str, value: Decimal):
            pdf.cell(sum(col_w[:-1]), 8, label, border=1, align="R")
            pdf.cell(col_w[-1], 8, f"{value:.2f}", border=1, align="R")
            pdf.ln(8)

        sub_total = invoice.sub_total or running_subtotal
        rcell("Sub Total", sub_total)

        if invoice.discount_amount:
            rcell(f"Discount ({invoice.discount_pct or Decimal('0'):.2f}%)", invoice.discount_amount)
        if invoice.tax_amount:
            rcell(f"Tax ({invoice.tax_pct or Decimal('0'):.2f}%)", invoice.tax_amount)

        grand_total = invoice.grand_total or (sub_total - (invoice.discount_amount or 0) + (invoice.tax_amount or 0))
        rcell("Grand Total", grand_total)

        if invoice.amount_paid:
            rcell("Amount Paid", invoice.amount_paid)
            rcell("Balance", grand_total - invoice.amount_paid)

        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, "Thank you.\nThis is a system-generated invoice.")

        return bytes(pdf.output(dest="S").encode("latin1"))

    def generate_and_save_invoice_pdf(self, invoice_id: int):

        inv = BillingService(self.db, self.tenant).get_invoice(invoice_id)

        filename = f"{inv['invoice_no'] or 'INV'}-{invoice_id}.pdf"
        rel_path = f"invoices/{filename}"

        tmp = Path("static/_tmp")
        tmp.mkdir(parents=True, exist_ok=True)
        pdf_tmp = tmp / filename

        c = canvas.Canvas(str(pdf_tmp), pagesize=A4)
        c.drawString(40, 800, f"Invoice: {inv['invoice_no']}")
        c.drawString(40, 780, f"Patient: {inv['patient_name']}")
        c.drawString(40, 760, f"Total: {inv['grand_total']}")
        c.showPage()
        c.save()

        data = pdf_tmp.read_bytes()
        abs_path = self.storage.save_bytes(rel_path, data)
        url = self.storage.url_for(rel_path)
        return abs_path, filename, url

    # def generate_and_save_invoice_pdf(self, invoice_id: int, storage, tenant) -> tuple[str, str, str | None]:
    #     """
    #     Returns (abs_path, filename, url). If backend can't make a URL, third item is None.
    #     """
    #
    #
    #     inv = self.get_invoice(invoice_id, tenant)  # dict from get_invoice()
    #     filename = f"{inv['invoice_no'] or 'INV'}-{invoice_id}.pdf"
    #     rel_path = f"invoices/{filename}"
    #
    #     # Render a minimal PDF (you can enrich later)
    #     tmp = Path("static/_tmp")
    #     tmp.mkdir(parents=True, exist_ok=True)
    #     pdf_tmp = tmp / filename
    #     c = canvas.Canvas(str(pdf_tmp), pagesize=A4)
    #     c.drawString(40, 800, f"Invoice: {inv['invoice_no']}")
    #     c.drawString(40, 780, f"Patient: {inv['patient_name']}")
    #     c.drawString(40, 760, f"Total: {inv['grand_total']}")
    #     y = 730
    #     for it in inv["items"]:
    #         c.drawString(40, y, f"- {it['description']}  x{it['qty']}  = {it['line_total']}")
    #         y -= 16
    #         if y < 60:
    #             c.showPage()
    #             y = 800
    #     c.showPage();
    #     c.save()
    #
    #     data = pdf_tmp.read_bytes()
    #     abs_path = storage.save_bytes(rel_path, data)  # LocalStorage returns absolute path
    #     url = storage.url_for(rel_path)  # likely None for LocalStorage
    #     return abs_path, filename, url

    # def generate_and_save_invoice_pdf(self, invoice_id: int) -> Tuple[str, str, str | None]:
    #     inv = self.db.get(Invoice, invoice_id)
    #     if not inv:
    #         raise ValueError(f"Invoice {invoice_id} not found")
    #
    #     pdf_bytes = self._render_pdf(inv)
    #     rel_path = self._relative_pdf_path(invoice_id)
    #     abs_or_url = self.storage.save_bytes(rel_path, pdf_bytes)
    #     filename = Path(rel_path).name
    #     public_url = self.storage.url_for(rel_path)
    #
    #     # Persist file info (local now; S3 later)
    #     inv.pdf_path = abs_or_url if public_url is None else None
    #     inv.pdf_url = public_url
    #     self.db.commit()
    #
    #     return abs_or_url, filename, public_url
