from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import async_get_db
from app.core.security import get_current_user
from app.models.pathology_notifications  import AppNotification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=list[dict])
def list_my_notifications(db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    rows = db.query(AppNotification).filter(AppNotification.user_id == user.id).order_by(AppNotification.id.desc()).limit(100).all()
    return [
        {"id": r.id, "event": r.event, "title": r.title, "body": r.body, "order_id": r.order_id,
         "data": r.data, "read_at": r.read_at, "created_at": r.created_at}
        for r in rows
    ]

@router.post("/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(async_get_db), user=Depends(get_current_user)):
    n = db.get(AppNotification, notif_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Not found")
    if not n.read_at:
        n.read_at = datetime.utcnow()
        db.commit()
    return {"ok": True}
