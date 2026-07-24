# from fastapi import HTTPException
# from sqlalchemy import select, func
# from app.db.session import SessionLocal
# from app.models.ipd import Floor, BedType, BedGroup, Bed
#
# class IPDMasterService:
#     # ---- UPSERT HELPERS ----
#     def bulk_upsert_floors(self, items: list[dict]) -> tuple[int, int]:
#         created = updated = 0
#         with SessionLocal() as db:
#             for it in items:
#                 name = it["name"].strip()
#                 obj = db.execute(select(Floor).where(Floor.name == name)).scalar_one_or_none()
#                 if obj:
#                     obj.description = it.get("description")
#                     updated += 1
#                 else:
#                     db.add(Floor(name=name, description=it.get("description")))
#                     created += 1
#             db.commit()
#         return created, updated
#
#     def bulk_upsert_bed_types(self, items: list[dict]) -> tuple[int, int]:
#         created = updated = 0
#         with SessionLocal() as db:
#             for it in items:
#                 name = it["name"].strip()
#                 obj = db.execute(select(BedType).where(BedType.name == name)).scalar_one_or_none()
#                 if obj:
#                     updated += 1
#                 else:
#                     db.add(BedType(name=name))
#                     created += 1
#             db.commit()
#         return created, updated
#
#     def bulk_upsert_bed_groups(self, items: list[dict]) -> tuple[int, int]:
#         created = updated = 0
#         with SessionLocal() as db:
#             for it in items:
#                 name = it["name"].strip()
#                 floor_name = it["floor_name"].strip()
#                 floor = db.execute(select(Floor).where(Floor.name == floor_name)).scalar_one_or_none()
#                 if not floor:
#                     raise HTTPException(status_code=400, detail=f"floor '{floor_name}' not found")
#                 obj = db.execute(
#                     select(BedGroup).where(BedGroup.name == name, BedGroup.floor_id == floor.id)
#                 ).scalar_one_or_none()
#                 if obj:
#                     obj.description = it.get("description")
#                     updated += 1
#                 else:
#                     db.add(BedGroup(name=name, description=it.get("description"), floor_id=floor.id))
#                     created += 1
#             db.commit()
#         return created, updated
#
#     def bulk_upsert_beds(self, items: list[dict]) -> tuple[int, int]:
#         created = updated = 0
#         with SessionLocal() as db:
#             for it in items:
#                 code = it["code"].strip()
#                 bt_name = it["bed_type_name"].strip()
#                 bg_name = it["bed_group_name"].strip()
#
#                 bt = db.execute(select(BedType).where(BedType.name == bt_name)).scalar_one_or_none()
#                 if not bt:
#                     raise HTTPException(status_code=400, detail=f"bed type '{bt_name}' not found")
#
#                 bg = db.execute(select(BedGroup).where(BedGroup.name == bg_name)).scalar_one_or_none()
#                 if not bg:
#                     raise HTTPException(status_code=400, detail=f"bed group '{bg_name}' not found")
#
#                 obj = db.execute(select(Bed).where(Bed.code == code)).scalar_one_or_none()
#                 if obj:
#                     obj.bed_type_id = bt.id
#                     obj.bed_group_id = bg.id
#                     updated += 1
#                 else:
#                     db.add(Bed(code=code, bed_type_id=bt.id, bed_group_id=bg.id, is_occupied=False))
#                     created += 1
#             db.commit()
#         return created, updated
#
#     # ---- READS ----
#     def bed_status_list(self) -> list[dict]:
#         with SessionLocal() as db:
#             stmt = (
#                 select(
#                     Bed.code,
#                     Bed.is_occupied,
#                     BedType.name.label("bt"),
#                     BedGroup.name.label("bg"),
#                     Floor.name.label("fl"),
#                 )
#                 .join(BedType, BedType.id == Bed.bed_type_id)
#                 .join(BedGroup, BedGroup.id == Bed.bed_group_id)
#                 .join(Floor, Floor.id == BedGroup.floor_id)
#                 .order_by(Floor.name.asc(), BedGroup.name.asc(), Bed.code.asc())
#             )
#             rows = db.execute(stmt).all()
#             result = []
#             for code, is_occ, bt, bg, fl in rows:
#                 result.append(
#                     {
#                         "bed_code": code,
#                         "bed_type": bt,
#                         "bed_group": bg,
#                         "floor": fl,
#                         "status": "Allotted" if is_occ else "Available",
#                     }
#                 )
#             return result


# app/services/ipd_master.py
from fastapi import HTTPException
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.ipd import Floor, BedType, BedGroup, Bed
from app.utils.tenant import Tenant
from app.services._tenant_utils import _set_tenant_fields, _filter_by_tenant

class IPDMasterService:
    def bulk_upsert_floors(self, items: list[dict], tenant: Tenant) -> tuple[int, int]:
        created = updated = 0
        with SessionLocal() as db:
            for it in items:
                name = it["name"].strip()
                stmt = _filter_by_tenant(select(Floor).where(Floor.name == name), Floor, tenant)
                obj = db.execute(stmt).scalar_one_or_none()
                if obj:
                    obj.description = it.get("description")
                    updated += 1
                else:
                    obj = Floor(name=name, description=it.get("description"))
                    _set_tenant_fields(obj, tenant)
                    db.add(obj)
                    created += 1
            db.commit()
        return created, updated

    def bulk_upsert_bed_types(self, items: list[dict], tenant: Tenant) -> tuple[int, int]:
        created = updated = 0
        with SessionLocal() as db:
            for it in items:
                name = it["name"].strip()
                stmt = _filter_by_tenant(select(BedType).where(BedType.name == name), BedType, tenant)
                obj = db.execute(stmt).scalar_one_or_none()
                if obj:
                    updated += 1
                else:
                    obj = BedType(name=name)
                    _set_tenant_fields(obj, tenant)
                    db.add(obj)
                    created += 1
            db.commit()
        return created, updated

    def bulk_upsert_bed_groups(self, items: list[dict], tenant: Tenant) -> tuple[int, int]:
        created = updated = 0
        with SessionLocal() as db:
            for it in items:
                name = it["name"].strip()
                floor_name = it["floor_name"].strip()
                fl_stmt = _filter_by_tenant(select(Floor).where(Floor.name == floor_name), Floor, tenant)
                floor = db.execute(fl_stmt).scalar_one_or_none()
                if not floor:
                    raise HTTPException(status_code=400, detail=f"floor '{floor_name}' not found")

                stmt = _filter_by_tenant(select(BedGroup).where(BedGroup.name == name, BedGroup.floor_id == floor.id), BedGroup, tenant)
                obj = db.execute(stmt).scalar_one_or_none()
                if obj:
                    obj.description = it.get("description")
                    updated += 1
                else:
                    obj = BedGroup(name=name, description=it.get("description"), floor_id=floor.id)
                    _set_tenant_fields(obj, tenant)
                    db.add(obj)
                    created += 1
            db.commit()
        return created, updated

    def bulk_upsert_beds(self, items: list[dict], tenant: Tenant) -> tuple[int, int]:
        created = updated = 0
        with SessionLocal() as db:
            for it in items:
                code = it["code"].strip()
                bt_name = it["bed_type_name"].strip()
                bg_name = it["bed_group_name"].strip()

                bt_stmt = _filter_by_tenant(select(BedType).where(BedType.name == bt_name), BedType, tenant)
                bt = db.execute(bt_stmt).scalar_one_or_none()
                if not bt:
                    raise HTTPException(status_code=400, detail=f"bed type '{bt_name}' not found")

                bg_stmt = _filter_by_tenant(select(BedGroup).where(BedGroup.name == bg_name), BedGroup, tenant)
                bg = db.execute(bg_stmt).scalar_one_or_none()
                if not bg:
                    raise HTTPException(status_code=400, detail=f"bed group '{bg_name}' not found")

                stmt = _filter_by_tenant(select(Bed).where(Bed.code == code), Bed, tenant)
                obj = db.execute(stmt).scalar_one_or_none()
                if obj:
                    obj.bed_type_id = bt.id
                    obj.bed_group_id = bg.id
                    updated += 1
                else:
                    obj = Bed(code=code, bed_type_id=bt.id, bed_group_id=bg.id, is_occupied=False)
                    _set_tenant_fields(obj, tenant)
                    db.add(obj)
                    created += 1
            db.commit()
        return created, updated

    def bed_status_list(self, tenant: Tenant) -> list[dict]:
        from sqlalchemy import select
        with SessionLocal() as db:
            stmt = (
                select(
                    Bed.code,
                    Bed.is_occupied,
                    BedType.name.label("bt"),
                    BedGroup.name.label("bg"),
                    Floor.name.label("fl"),
                )
                .join(BedType, BedType.id == Bed.bed_type_id)
                .join(BedGroup, BedGroup.id == Bed.bed_group_id)
                .join(Floor, Floor.id == BedGroup.floor_id)
            )
            stmt = _filter_by_tenant(stmt, Bed, tenant)
            rows = db.execute(stmt.order_by(Floor.name.asc(), BedGroup.name.asc(), Bed.code.asc())).all()
            return [
                {
                    "bed_code": code,
                    "bed_type": bt,
                    "bed_group": bg,
                    "floor": fl,
                    "status": "Allotted" if is_occ else "Available",
                }
                for code, is_occ, bt, bg, fl in rows
            ]
