from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_scan import RadiologyScan


class RadiologyScanService:

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # CREATE SCAN
    # ========================================
    def create_scan(
        self,
        appointment_id: int,
        technician_name: str | None,
        remarks: str | None,
    ):

        # Check whether a scan already exists
        # for this appointment
        existing_scan = (
            self.db.query(RadiologyScan)
            .filter(
                RadiologyScan.appointment_id
                == appointment_id
            )
            .first()
        )

        if existing_scan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A scan already exists "
                    "for this appointment."
                )
            )

        # Create new scan
        scan = RadiologyScan(
            appointment_id=appointment_id,
            status="Pending",
            technician_name=technician_name,
            remarks=remarks,
        )

        self.db.add(scan)

        self.db.commit()

        self.db.refresh(scan)

        return scan

    # ========================================
    # GET ALL SCANS
    # ========================================
    def get_all_scans(self):

        return (
            self.db.query(RadiologyScan)
            .order_by(
                RadiologyScan.id.desc()
            )
            .all()
        )

    # ========================================
    # GET SCAN BY ID
    # ========================================
    def get_scan(
        self,
        scan_id: int
    ):

        scan = (
            self.db.query(RadiologyScan)
            .filter(
                RadiologyScan.id == scan_id
            )
            .first()
        )

        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology scan not found."
            )

        return scan

    # ========================================
    # START SCAN
    # ========================================
    def start_scan(
        self,
        scan_id: int
    ):

        scan = self.get_scan(scan_id)

        # Scan can only start from Pending
        if scan.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Scan can only be started "
                    "when the status is Pending."
                )
            )

        scan.status = "In Progress"

        scan.started_at = datetime.utcnow()

        self.db.commit()

        self.db.refresh(scan)

        return scan

    # ========================================
    # COMPLETE SCAN
    # ========================================
    def complete_scan(
        self,
        scan_id: int
    ):

        scan = self.get_scan(scan_id)

        # Scan can only be completed
        # when it is In Progress
        if scan.status != "In Progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Scan can only be completed "
                    "when the status is In Progress."
                )
            )

        scan.status = "Completed"

        scan.completed_at = datetime.utcnow()

        self.db.commit()

        self.db.refresh(scan)

        return scan

    # ========================================
    # UPDATE SCAN
    # ========================================
    def update_scan(
        self,
        scan_id: int,
        technician_name: str | None,
        remarks: str | None,
    ):

        scan = self.get_scan(scan_id)

        if technician_name is not None:
            scan.technician_name = technician_name

        if remarks is not None:
            scan.remarks = remarks

        self.db.commit()

        self.db.refresh(scan)

        return scan

    # ========================================
    # DELETE SCAN
    # ========================================
    def delete_scan(
        self,
        scan_id: int
    ):

        scan = self.get_scan(scan_id)

        self.db.delete(scan)

        self.db.commit()

        return {
            "message": (
                "Radiology scan "
                "deleted successfully."
            )
        }