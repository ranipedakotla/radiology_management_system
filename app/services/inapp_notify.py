# from typing import DefaultDict, List
# from collections import defaultdict
# from fastapi import WebSocket
#
# class WSManager:
#     def __init__(self):
#         self._conns: DefaultDict[int, List[WebSocket]] = defaultdict(list)
#
#     async def connect(self, user_id: int, ws: WebSocket):
#         await ws.accept()
#         self._conns[user_id].append(ws)
#
#     async def disconnect(self, user_id: int, ws: WebSocket):
#         if ws in self._conns[user_id]:
#             self._conns[user_id].remove(ws)
#
#     async def send_to(self, user_id: int, payload: dict):
#         for ws in list(self._conns[user_id]):
#             try:
#                 await ws.send_json(payload)
#             except Exception:
#                 await self.disconnect(user_id, ws)
#
# manager = WSManager()
#
# # helper used earlier
# async def notify_user(db, user_id: int, **payload):
#     # persist to DB if you do that, then:
#     await manager.send_to(user_id, payload)
#
# async def notify_many(db, user_ids, **payload):
#     for uid in user_ids:
#         await notify_user(db, uid, **payload)
#


#
# # app/services/inapp_notify.py
# from typing import DefaultDict, List
# from collections import defaultdict
# from fastapi import WebSocket
#
# # from __future__ import annotations
# from typing import Iterable, Any
# from datetime import datetime
# import json
# from sqlalchemy.orm import Session
# from sqlalchemy import select
# from app.models.notifications import AppNotification
# # from app.routers.notifications_ws import manager  # your WS connection manager
#
#
# class WSManager:
#     def __init__(self):
#         self._conns: DefaultDict[int, List[WebSocket]] = defaultdict(list)
#
#     async def connect(self, user_id: int, ws: WebSocket):
#         await ws.accept()
#         self._conns[user_id].append(ws)
#
#     async def disconnect(self, user_id: int, ws: WebSocket):
#         if ws in self._conns[user_id]:
#             self._conns[user_id].remove(ws)
#
#     async def send_to(self, user_id: int, payload: dict):
#         for ws in list(self._conns[user_id]):
#             try:
#                 await ws.send_json(payload)
#             except Exception:
#                 await self.disconnect(user_id, ws)
#
# manager = WSManager()
#
# async def notify_user(
#     db: Session,
#     user_id: int,
#     *,
#     event: str,
#     title: str,
#     body: str,
#     order_id: int | None = None,
#     data: dict[str, Any] | None = None,
# ) -> AppNotification:
#     """Insert a notification row (commit!) and try WS push.
#        Always commit to DB even if WS delivery fails.
#     """
#     note = AppNotification(
#         user_id=user_id,
#         event=event,
#         title=title,
#         body=body,
#         order_id=order_id,
#         data_json=json.dumps(data or {}),
#         read=False,
#         created_at=datetime.utcnow(),
#     )
#     db.add(note)
#     # Flush+commit so it's visible to readers and survives even if WS send fails
#     db.flush()
#     db.commit()
#     db.refresh(note)
#
#     # WebSocket push is best-effort; never block DB insert
#     payload = {
#         "id": note.id,
#         "event": note.event,
#         "title": note.title,
#         "body": note.body,
#         "order_id": note.order_id,
#         "data": data or {},
#         "created_at": note.created_at.isoformat() + "Z",
#         "read": note.read,
#     }
#     try:
#         # if user connected, this sends; otherwise it’s fine (row is in DB)
#         await manager.send_personal_message(user_id, payload)
#     except Exception as e:
#         # log and swallow—DB row is already committed
#         print(f"[notify_user] WS send failed user={user_id}: {e}")
#
#     return note
#
#
# async def notify_many(
#     db: Session,
#     user_ids: Iterable[int],
#     *,
#     event: str,
#     title: str,
#     body: str,
#     order_id: int | None = None,
#     data: dict[str, Any] | None = None,
# ) -> list[AppNotification]:
#     out: list[AppNotification] = []
#     for uid in set(user_ids):
#         try:
#             n = await notify_user(
#                 db, uid, event=event, title=title, body=body, order_id=order_id, data=data
#             )
#             out.append(n)
#         except Exception as e:
#             print(f"[notify_many] failed user={uid}: {e}")
#     return out


# app/services/inapp_notify.py  (patch)

from typing import DefaultDict, List, Iterable, Any
from collections import defaultdict
from datetime import datetime
import json
from fastapi import WebSocket
from sqlalchemy import null
from sqlalchemy.orm import Session
from app.models.pathology_notifications import AppNotification

class WSManager:
    def __init__(self):
        self._conns: DefaultDict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self._conns[user_id].append(ws)

    async def disconnect(self, user_id: int, ws: WebSocket):
        if ws in self._conns[user_id]:
            self._conns[user_id].remove(ws)

    async def send_to(self, user_id: int, payload: dict):
        for ws in list(self._conns[user_id]):
            try:
                await ws.send_json(payload)
            except Exception:
                await self.disconnect(user_id, ws)

manager = WSManager()

async def notify_user(
    db: Session,
    user_id: int,
    *,
    event: str,
    title: str,
    body: str,
    order_id: int | None = None,
    data: dict[str, Any] | None = None,
) -> AppNotification:
    # 🔧 USE THE COLUMN YOUR MODEL HAS:
    # - If your AppNotification has `data` (JSON/Text): set `data=...`
    # - If it has `data_json`: change code & model consistently (see Option B below)

    # OPTION A (most likely): model has `data` column
    note = AppNotification(
        user_id=user_id,
        event=event,
        title=title,
        body=body,
        order_id=order_id,
        # If `data` is JSON type in DB ORM, assign dict directly; if it's Text, json.dumps it.
        # data=json.dumps(data or {}),   # <-- if model.data is Text
        data=(data or {}),           # <-- if model.data is JSON type
        read_at=None,
        created_at=datetime.utcnow(),
    )

    db.add(note)
    db.flush()
    db.commit()
    db.refresh(note)

    payload = {
        "id": note.id,
        "event": note.event,
        "title": note.title,
        "body": note.body,
        "order_id": note.order_id,
        "data": data or {},
        "created_at": note.created_at.isoformat() + "Z",
        "read": note.read_at,
    }
    try:
        # 🔧 call the method you actually implemented
        await manager.send_to(user_id, payload)
    except Exception as e:
        print(f"[notify_user] WS send failed user={user_id}: {e}")

    return note

async def notify_many(
    db: Session,
    user_ids: Iterable[int],
    *,
    event: str,
    title: str,
    body: str,
    order_id: int | None = None,
    data: dict[str, Any] | None = None,
) -> list[AppNotification]:
    out: list[AppNotification] = []
    for uid in set(user_ids):
        try:
            n = await notify_user(
                db, uid, event=event, title=title, body=body, order_id=order_id, data=data
            )
            out.append(n)
        except Exception as e:
            print(f"[notify_many] failed user={uid}: {e}")
    return out
