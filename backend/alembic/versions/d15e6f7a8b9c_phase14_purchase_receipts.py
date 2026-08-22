"""add durable purchase receipt idempotency

Revision ID: d15e6f7a8b9c
Revises: c14d5e6f7a8b
"""

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql
from alembic import op

revision = "d15e6f7a8b9c"
down_revision = "c14d5e6f7a8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_receipts",
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_purchase_receipts_org_key"),
    )
    op.create_index("ix_purchase_receipts_purchase_order_id", "purchase_receipts", ["purchase_order_id"])
    op.create_index("ix_purchase_receipts_organization_id", "purchase_receipts", ["organization_id"])
    op.create_table(
        "purchase_receipt_items",
        sa.Column("receipt_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_item_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["receipt_id"], ["purchase_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_item_id"], ["purchase_order_items.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("receipt_id", "purchase_order_item_id", name="uq_purchase_receipt_item"),
    )


def downgrade() -> None:
    op.drop_table("purchase_receipt_items")
    op.drop_index("ix_purchase_receipts_organization_id", table_name="purchase_receipts")
    op.drop_index("ix_purchase_receipts_purchase_order_id", table_name="purchase_receipts")
    op.drop_table("purchase_receipts")