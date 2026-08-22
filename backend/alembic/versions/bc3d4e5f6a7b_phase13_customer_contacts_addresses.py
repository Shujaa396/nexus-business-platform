"""add phase 13 customer contacts and addresses

Revision ID: bc3d4e5f6a7b
Revises: bb2c3d4e5f6a
"""

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

from alembic import op

revision = "bc3d4e5f6a7b"
down_revision = "bb2c3d4e5f6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_contacts",
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("job_title", sa.String(length=120), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_contacts_organization_id", "customer_contacts", ["organization_id"])
    op.create_index("ix_customer_contacts_customer_id", "customer_contacts", ["customer_id"])
    op.create_table(
        "customer_addresses",
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("address_type", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("postal_code", sa.String(length=40), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_addresses_organization_id", "customer_addresses", ["organization_id"])
    op.create_index("ix_customer_addresses_customer_id", "customer_addresses", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_customer_addresses_customer_id", table_name="customer_addresses")
    op.drop_index("ix_customer_addresses_organization_id", table_name="customer_addresses")
    op.drop_table("customer_addresses")
    op.drop_index("ix_customer_contacts_customer_id", table_name="customer_contacts")
    op.drop_index("ix_customer_contacts_organization_id", table_name="customer_contacts")
    op.drop_table("customer_contacts")