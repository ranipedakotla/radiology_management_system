from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0010_invoice_pdf_cols"
down_revision = "0010_billing_auto_items_support"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("invoices") as batch:
        batch.add_column(sa.Column("pdf_path", sa.String(length=500), nullable=True))
        batch.add_column(sa.Column("pdf_url", sa.String(length=500), nullable=True))

def downgrade():
    with op.batch_alter_table("invoices") as batch:
        batch.drop_column("pdf_url")
        batch.drop_column("pdf_path")
