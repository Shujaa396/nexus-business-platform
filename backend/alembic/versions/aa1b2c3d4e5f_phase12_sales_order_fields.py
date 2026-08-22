"""add phase 12 sales order fields

Revision ID: aa1b2c3d4e5f
Revises: 9c2d3e4f5a6b
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

revision = "aa1b2c3d4e5f"
down_revision = "9c2d3e4f5a6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("warehouse_id", psql.UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("requested_fulfillment_date", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_orders_warehouse_id", "orders", "warehouses", ["warehouse_id"], ["id"], ondelete="RESTRICT")
    op.add_column("order_items", sa.Column("fulfilled_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("order_items", "fulfilled_quantity")
    op.drop_constraint("fk_orders_warehouse_id", "orders", type_="foreignkey")
    op.drop_column("orders", "requested_fulfillment_date")
    op.drop_column("orders", "warehouse_id")
