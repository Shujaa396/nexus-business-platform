"""add phase 13 customer crm fields

Revision ID: bb2c3d4e5f6a
Revises: aa1b2c3d4e5f
"""

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from alembic import op

revision = "bb2c3d4e5f6a"
down_revision = "aa1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("customers") as batch:
        batch.add_column(sa.Column("customer_code", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("company_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("billing_address", sa.Text(), nullable=True))
        batch.add_column(sa.Column("shipping_address", sa.Text(), nullable=True))
        batch.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"))
        batch.add_column(sa.Column("credit_limit", sa.Numeric(18, 4), nullable=False, server_default="0"))
        batch.add_column(sa.Column("discount_percent", sa.Numeric(5, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("user_id", psql.UUID(as_uuid=True), nullable=True))
        batch.create_unique_constraint("uq_customers_organization_code", ["organization_id", "customer_code"])
        batch.create_unique_constraint("uq_customers_user_id", ["user_id"])
        batch.create_index("ix_customers_status", ["status"])
        batch.create_foreign_key("fk_customers_user_id", "users", ["user_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("customers") as batch:
        batch.drop_constraint("fk_customers_user_id", type_="foreignkey")
        batch.drop_index("ix_customers_status")
        batch.drop_constraint("uq_customers_user_id", type_="unique")
        batch.drop_constraint("uq_customers_organization_code", type_="unique")
        for column in ("user_id", "discount_percent", "credit_limit", "status", "shipping_address", "billing_address", "company_name", "customer_code"):
            batch.drop_column(column)