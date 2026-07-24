# app/scripts/bootstrap_minimal.py
from datetime import datetime
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.org import Hospital, Branch
from app.models.auth import User, Role

ROLES = [
    "superadmin","admin","receptionist","doctor","nurse","accountant",
    "pharmacy_admin","pathology_admin","radiology_admin"
]

def get_or_create_hospital(db, name: str) -> Hospital:
    inst = db.query(Hospital).filter_by(name=name).first()
    if inst:
        return inst
    inst = Hospital(name=name, is_active=True)
    db.add(inst); db.flush()
    return inst

def get_or_create_branch(db, hospital_id: int, name: str, code: str) -> Branch:
    # Prefer matching by (hospital_id, code) since code is unique
    inst = db.query(Branch).filter_by(hospital_id=hospital_id, code=code).first()
    if inst:
        # Keep name in sync if it changed
        if inst.name != name:
            inst.name = name
        return inst
    inst = Branch(hospital_id=hospital_id, name=name, code=code, is_active=True)
    db.add(inst); db.flush()
    return inst

def get_or_create_role(db, name: str) -> Role:
    inst = db.query(Role).filter_by(name=name).first()
    if inst:
        return inst
    inst = Role(name=name)
    db.add(inst); db.flush()
    return inst

def main():
    db = SessionLocal()
    try:
        hosp = get_or_create_hospital(db, "Alpha Health")

        # *** IMPORTANT: provide a non-null, unique code for the branch ***
        branch = get_or_create_branch(db, hosp.id, name="Main Branch", code="MAIN")

        # roles
        for rn in ROLES:
            get_or_create_role(db, rn)

        # superadmin user (attach hospital + branch)
        user = db.query(User).filter_by(email="lucky@gmail.com").first()
        if not user:
            user = User(
                email="lucky@gmail.com",
                password_hash=hash_password("lucky143"),
                is_active=True,
                hospital_id=hosp.id,
                current_branch_id=branch.id,
                last_login_at=None,
            )
            db.add(user); db.flush()
        else:
            # ensure tenant context is set
            user.hospital_id = user.hospital_id or hosp.id
            user.current_branch_id = user.current_branch_id or branch.id

        # attach roles to user
        have = {r.name for r in user.roles}
        need = set(ROLES) - have
        if need:
            role_map = {r.name: r for r in db.query(Role).filter(Role.name.in_(list(need))).all()}
            for rn in need:
                if rn in role_map:
                    user.roles.append(role_map[rn])

        db.commit()
        print(f"OK: hospital={hosp.id}, branch={branch.id} ({branch.code}), user={user.id}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
