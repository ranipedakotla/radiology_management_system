from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_registration import RadiologyRegistration
from app.models.radiology_scan import RadiologyScan


class RadiologyScanService:

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------
    # Start Scan
    # --------------------------------
    def start_scan(
            self,
            registration_id: int,
            technician_name: str | None,
    ):

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(
                RadiologyRegistration.id == registration_id
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology registration not found."
            )

        scan = RadiologyScan(
            registration_id=registration_id,
            technician_name=technician_name,
            scan_status="In Progress",
            started_at=datetime.utcnow()
        )

        registration.scan_status = "In Progress"

        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)

        return scan

    # --------------------------------
    # Get All Scans
    # --------------------------------
    def get_all_scans(self):

        return (
            self.db.query(RadiologyScan)
            .order_by(RadiologyScan.id.desc())
            .all()
        )

    # --------------------------------
    # Get Scan
    # --------------------------------
    def get_scan(
        self,
        scan_id: int
    ):

        scan = (
            self.db.query(RadiologyScan)
            .filter(RadiologyScan.id == scan_id)
            .first()
        )

        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found."
            )

        return scan

    # --------------------------------
    # Complete Scan
    # --------------------------------
    def complete_scan(
        self,
        scan_id: int
    ):

        scan = self.get_scan(scan_id)

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(
                RadiologyRegistration.id ==
                scan.registration_id
            )
            .first()
        )

        scan.scan_status = "Completed"
        scan.completed_at = datetime.utcnow()

        registration.scan_status = "Completed"
        registration.status = "Completed"

        self.db.commit()
        self.db.refresh(scan)

        return scan

    # --------------------------------
    # Hold Scan
    # --------------------------------
    def hold_scan(
        self,
        scan_id: int,
        hold_reason: str
    ):

        scan = self.get_scan(scan_id)

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(
                RadiologyRegistration.id ==
                scan.registration_id
            )
            .first()
        )

        scan.scan_status = "Hold"
        scan.hold_reason = hold_reason

        registration.scan_status = "Hold"

        self.db.commit()
        self.db.refresh(scan)

        return scan

    # --------------------------------
    # Cancel Scan
    # --------------------------------
    def cancel_scan(
        self,
        scan_id: int,
        cancellation_reason: str
    ):

        scan = self.get_scan(scan_id)

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(
                RadiologyRegistration.id ==
                scan.registration_id
            )
            .first()
        )

        scan.scan_status = "Cancelled"
        scan.cancellation_reason = cancellation_reason

        registration.scan_status = "Cancelled"
        registration.status = "Cancelled"

        self.db.commit()
        self.db.refresh(scan)

        return scan

    # --------------------------------
    # Reschedule Scan
    # --------------------------------
    def reschedule_scan(
        self,
        scan_id: int,
        reschedule_date: datetime
    ):

        scan = self.get_scan(scan_id)

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(
                RadiologyRegistration.id ==
                scan.registration_id
            )
            .first()
        )

        scan.scan_status = "Pending"
        scan.reschedule_date = reschedule_date

        registration.scan_status = "Pending"

        self.db.commit()
        self.db.refresh(scan)

        return scan

    # --------------------------------
    # Get Scan By Registration ID
    # --------------------------------
    def get_scan_by_registration(
        self,
        registration_id: int
    ):

        scan = (
            self.db.query(RadiologyScan)
            .filter(
                RadiologyScan.registration_id ==
                registration_id
            )
            .first()
        )

        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found."
            )

        return scan