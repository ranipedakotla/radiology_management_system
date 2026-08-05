from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


from app.models import *
from app.db.base import Base
from app.db.session import engine
from app.db.session import async_engine

from app.core.settings import settings

# routers (each router already has its own subpath prefix like "/auth", "/appointments", etc.)
from app.api.v1.routes import auth as auth_routes, ambulance_billing
from app.api.v1.routes import appointments as appt_routes
from app.api.v1.routes import opd as opd_routes
from app.api.v1.routes import stats as stats_routes
from app.api.v1.routes import admin_people as admin_people_routes
from app.api.v1.routes import billing as billing_routes         # NOTE: this router already has "/api/v1/billing"
from app.api.v1.routes import ipd as ipd_routes                 # prefix="/ipd" inside router
from app.api.v1.routes import ipd_master as ipd_master_routes   # NOTE: this router already has "/api/v1/ipd/master"
from app.api.v1.routes import admin_org as hospital_branches
from app.api.v1.routes.lab_tests import router as lab_tests
from app.api.v1.routes.radiology_patient import router as radiology_patient
from app.api.v1.routes.radiology_registration import router as radiology_registration

from app.api.v1.routes.radiology_scan import router as radiology_scan
from app.api.v1.routes.radiology_refund import router as radiology_refund
from app.api.v1.routes.radiology_report import router as radiology_report

from contextlib import asynccontextmanager


from app.api.v1.routes.vendor_router import router as vendor_router
from app.api.v1.routes.quotation_router import router as quotation_router
from app.api.v1.routes.purchase_router import router as purchase_router
from app.api.v1.routes.discount_router import router as discount_router
# from app.routers.shiftrouter import router as shiftrouter
from app.api.v1.routes.billingrouter import router as billingrouter
from app.api.v1.routes.opd_router import router as opd_router
from app.api.v1.routes.accounting_router import router as accounting_router
from app.api.v1.routes.return_router import router as return_router
from app.api.v1.routes.pharmacy_router import router as pharmacy_router
# from app.routers.prescription_router import router as prescription_router
import sys
import os
from dotenv import load_dotenv


from app.services import authenticate_ws_token
from app.services.inapp_notify import manager

#add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
from app.api.v1.routes.ipd_router import router as ipd_router
# from app.api.v1.routes.auth_router import router as auth_router
from app.api.v1.routes.pharmacist_router import router as pharmacist_router
from app.api.v1.routes.admin_router import router as admin_router
from app.api.v1.routes.superadmin_router import router as superadmin_router
# from app.routers.medicines_router import router as medicines_router
# from app.routers.vendors_router import router as vendors_router
# from app.routers.quotations_router import router as quotations_router
from app.api.v1.routes.entry_medicine import router as medicine_router
from app.api.v1.routes.medicine_batch import router as batch_router
from app.api.v1.routes.reports import router as reports_router
from app.api.v1.routes.grn import router as grn
from app.api.v1.routes.surgical import router as surgical_item_router, surgical_batch_router
# from app.routers.non_surgical import router as non_surgical_item_router, non_surgical_batch_router
from app.api.v1.routes.non_surgical import (
    non_surgical_item_router,
    non_surgical_batch_router,
)

from app.api.v1.routes.pharmacy_issue import router as pharmacy_issue_router
from app.api.v1.routes.hospital import  router as hospital_router
from app.api.v1.routes.branches import router as branches_router

from app.api.v1.routes.blood_bank_router import router as bloodbank_router

from app.api.v1.routes.ambulance_report import router as ambulance_report
from app.api.v1.routes.ambulance import router as ambulance
from app.api.v1.routes.ambulance_driver import router as ambulance_driver
from app.api.v1.routes.ambulance_invoice import router as ambulance_invoice
from app.api.v1.routes.ambulance_billing import router as ambulance_billing
from app.api.v1.routes.pathology_billing import router as pathology_billing
from app.api.v1.routes.pathology_reports import router as pathology_reports
from app.api.v1.routes.pathology_orders import router  as pathology_orders
from app.api.v1.routes.pathology_notifications import router  as  pathology_notifications
from app.api.v1.routes.catalog import router as catalog
from app.api.v1.routes.radiology_invoice import router as radiology_invoice



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Base.metadata.create_all(bind=engine)
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#
# # app = FastAPI(title=settings.APP_NAME)
# app = FastAPI(
#     title=settings.APP_NAME,
#     lifespan=lifespan
# )

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# CORS first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static only if present (prevents startup error on fresh envs)
static_dir = Path("app/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# All subpath routers get the global API prefix
app.include_router(auth_routes.router,        prefix=settings.API_PREFIX)
app.include_router(appt_routes.router,        prefix=settings.API_PREFIX)
app.include_router(opd_routes.router,         prefix=settings.API_PREFIX)
app.include_router(stats_routes.router,       prefix=settings.API_PREFIX)
app.include_router(admin_people_routes.router,prefix=settings.API_PREFIX)
app.include_router(ipd_routes.router,         prefix=settings.API_PREFIX)  # <— FIXED (no extra /ipd)
app.include_router(hospital_branches.router)

# These two already include "/api/v1" inside the router prefix — include as-is to avoid double-prefix
app.include_router(billing_routes.router)
app.include_router(ipd_master_routes.router)
app.include_router(lab_tests)
app.include_router(radiology_patient)
app.include_router(radiology_registration)
app.include_router(radiology_scan)
app.include_router(radiology_refund)
app.include_router(radiology_invoice)
app.include_router(radiology_report)


#include all routers
# app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(pharmacist_router, prefix="/pharmacy", tags=["Pharmacist"])
app.include_router(ipd_router, prefix="/ipd", tags=["IPD Pharmacy"])
app.include_router(admin_router, prefix="/pharmacy", tags=["Admin"])
app.include_router(superadmin_router, prefix="/superadmin", tags=["Superadmin"])
# app.include_router(medicines_router)
# app.include_router(shiftrouter)
# app.include_router(vendors_router)
# app.include_router(quotations_router)
app.include_router(hospital_router)
app.include_router(branches_router)

app.include_router(grn)
app.include_router(medicine_router)
app.include_router(batch_router)
app.include_router(reports_router)
app.include_router(pharmacy_issue_router)
app.include_router(surgical_item_router, tags=["Surgical Items"])
app.include_router(surgical_batch_router, tags=["Surgical Batches"])
app.include_router(non_surgical_item_router)
app.include_router(non_surgical_batch_router)



# app.include_router(medicine_router)
app.include_router(vendor_router)
app.include_router(quotation_router)
app.include_router(purchase_router)
app.include_router(discount_router)
# app.include_router(shiftrouter)
app.include_router(billingrouter)
app.include_router(opd_router)
app.include_router(accounting_router)
app.include_router(pharmacy_router)
app.include_router(return_router)

# ambulance routers
app.include_router(ambulance_billing)
app.include_router(ambulance_driver)
app.include_router(ambulance_invoice)
app.include_router(ambulance_report)
app.include_router(ambulance)

app.include_router(bloodbank_router)

# pathology
app.include_router(pathology_notifications)
app.include_router(pathology_orders)
app.include_router(pathology_reports)
app.include_router(pathology_billing)
app.include_router(catalog)

@app.get("/")
def root():
    return {"ok": True, "app": settings.APP_NAME}


# from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import WebSocket, WebSocketDisconnect, Depends
# from app.ws.manager import manager
# from app.ws.auth_ws import authenticate_ws_token
#
# from app.core.config import settings
# from app.routers import auth as auth_router
# from app.routers import admin_users as admin_users_router
# from app.routers import patients as patients_router
# from app.routers import doctors as doctors_router
# from app.routers import catalog as catalog_router
# from app.routers import orders as orders_router
# from app.routers import reports as reports_router
# from app.routers import billing as billing_router
# from app.routers import doctor_signatures as doc_sig
# from app.routers import notifications as notifications_router
# from app.routers import notifications_ws
#
#
# app = FastAPI(title=settings.APP_NAME)
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth_router.router)
# app.include_router(admin_users_router.router)
# app.include_router(patients_router.router)
# app.include_router(doctors_router.router)
# app.include_router(catalog_router.router)
# app.include_router(orders_router.router)
# app.include_router(reports_router.router)
# app.include_router(billing_router.router)
# app.include_router(doc_sig.router)
# app.include_router(notifications_router.router)
# app.include_router(notifications_ws.router)
# @app.get("/health")
# def health():
#     return {"ok": True, "env": settings.ENV}
#
#
# def authenticate_ws_token(token):
#     pass


@app.websocket("/ws/notifications")
async def ws_notifications(ws: WebSocket):
    # client must connect with: /ws/notifications?token=JWT
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return
    try:
        u = authenticate_ws_token(token)
    except Exception:
        await ws.close(code=4401)
        return

    await manager.connect(u.id, ws)
    try:
        while True:
            # We keep the socket open. If you want to support client pings or acks, read here:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(u.id, ws)
