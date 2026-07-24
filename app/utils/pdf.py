# app/utils/pdf.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pathlib import Path

def generate_receipt_pdf(receipt, invoice, patient) -> str:
    out = Path("static/receipts")
    out.mkdir(parents=True, exist_ok=True)
    pdf_path = out / f"{receipt.receipt_no}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    # draw header, hospital, patient, table of items, totals...
    c.drawString(40, 800, f"Receipt: {receipt.receipt_no}")
    c.drawString(40, 780, f"Patient: {patient.first_name} {patient.last_name}")
    # ...
    c.showPage(); c.save()
    return str(pdf_path)
