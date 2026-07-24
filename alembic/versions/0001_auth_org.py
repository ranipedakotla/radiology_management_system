from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '0001_auth_org'
down_revision = None
branch_labels = None
depends_on = None

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES = [
    "superadmin","admin","accountant","doctor","receptionist","pharmacist","pathologist","radiologist","nurse"
]

PERMS = [
    "users.read","users.create","users.update","users.disable",
    "appointments.read","appointments.book","appointments.update","appointments.cancel",
    "opd.read","opd.create_visit","opd.update_visit","prescriptions.create",
    "ipd.read","ipd.admit","ipd.transfer","ipd.discharge","ipd.charge.add",
    "billing.read","invoice.create","receipt.create","refund.create"
]

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(120), nullable=False, unique=True, index=True),
        sa.Column('phone', sa.String(20), unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )
    op.create_table('roles',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(40), nullable=False, unique=True, index=True),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default=sa.text('1')),
    )
    op.create_table('permissions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('code', sa.String(80), nullable=False, unique=True, index=True),
        sa.Column('description', sa.String(255), nullable=True),
    )
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', sa.Integer, sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table('hospitals',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
    )

    # seed roles, permissions, superadmin
    conn = op.get_bind()

    # ✅ FIX: executemany with a single placeholder
    conn.execute(
        sa.text("INSERT INTO roles(name, is_system) VALUES (:name, 1)"),
        [{"name": r} for r in ROLES],
    )
    conn.execute(
        sa.text("INSERT INTO permissions(code) VALUES (:code)"),
        [{"code": p} for p in PERMS],
    )

    # map simple default perms to roles (admin gets all)
    role_ids = {r: conn.execute(sa.text("SELECT id FROM roles WHERE name=:n"), {"n": r}).scalar() for r in ROLES}
    perm_ids = {c: conn.execute(sa.text("SELECT id FROM permissions WHERE code=:c"), {"c": c}).scalar() for c in PERMS}

    def grant(role, codes):
        for code in codes:
            conn.execute(sa.text("INSERT INTO role_permissions(role_id,permission_id) VALUES (:r,:p)"),
                         {"r": role_ids[role], "p": perm_ids[code]})

    # admin & superadmin get all
    for role in ("admin","superadmin"):
        for c in PERMS:
            grant(role, [c])

    # receptionist
    for c in ["appointments.read","appointments.book","appointments.update","appointments.cancel","users.read"]:
        grant("receptionist", [c])

    # doctor
    for c in ["opd.read","opd.create_visit","opd.update_visit","prescriptions.create","appointments.read"]:
        grant("doctor", [c])

    # nurse
    for c in ["ipd.read"]:
        grant("nurse", [c])

    # accountant
    for c in ["billing.read","invoice.create","receipt.create","refund.create"]:
        grant("accountant", [c])

    # create superadmin user (email/pass)
    password_hash = pwd.hash("admin123")
    conn.execute(sa.text("INSERT INTO users(email,password_hash,is_active) VALUES (:e,:p,1)"),
                 {"e": "admin@hms.local", "p": password_hash})
    uid = conn.execute(sa.text("SELECT id FROM users WHERE email=:e"), {"e": "admin@hms.local"}).scalar()
    conn.execute(sa.text("INSERT INTO user_roles(user_id,role_id) VALUES (:u,:r)"),
                 {"u": uid, "r": role_ids["superadmin"]})


def downgrade():
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('hospitals')
