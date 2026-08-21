"""add phase 10 purchase orders

Revision ID: 8b1c2d3e4f5a
Revises: 7a9b8c6d5e4f
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

revision = "8b1c2d3e4f5a"
down_revision = "7a9b8c6d5e4f"
branch_labels = None
depends_on = None


STATUS_CHECK = "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'CANCELLED')"


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 4), nullable=False),
        sa.Column("tax", sa.Numeric(18, 4), nullable=False),
        sa.Column("discount", sa.Numeric(18, 4), nullable=False),
        sa.Column("total", sa.Numeric(18, 4), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(STATUS_CHECK, name="ck_purchase_orders_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "purchase_order_number", name="uq_purchase_orders_org_number"),
    )
    op.create_index("ix_purchase_orders_organization_id", "purchase_orders", ["organization_id"])
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"])
    op.create_index("ix_purchase_orders_branch_id", "purchase_orders", ["branch_id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])
    op.create_index("ix_purchase_orders_order_date", "purchase_orders", ["order_date"])

    op.create_table(
        "purchase_order_items",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("received_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), nullable=False),
        sa.Column("subtotal", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_order_id", "product_id", name="uq_purchase_order_items_order_product"),
    )
    op.create_index("ix_purchase_order_items_purchase_order_id", "purchase_order_items", ["purchase_order_id"])
    op.create_index("ix_purchase_order_items_product_id", "purchase_order_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_purchase_order_items_product_id", table_name="purchase_order_items")
    op.drop_index("ix_purchase_order_items_purchase_order_id", table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_order_date", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_branch_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_organization_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
