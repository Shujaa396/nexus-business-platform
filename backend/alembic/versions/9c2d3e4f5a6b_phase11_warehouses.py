"""add phase 11 warehouse inventory management

Revision ID: 9c2d3e4f5a6b
Revises: 8b1c2d3e4f5a
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

revision = "9c2d3e4f5a6b"
down_revision = "8b1c2d3e4f5a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_warehouses_organization_code"),
    )
    op.create_index("ix_warehouses_organization_id", "warehouses", ["organization_id"])
    op.create_index("ix_warehouses_branch_id", "warehouses", ["branch_id"])

    op.add_column("purchase_orders", sa.Column("warehouse_id", psql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_purchase_orders_warehouse_id", "purchase_orders", "warehouses", ["warehouse_id"], ["id"], ondelete="RESTRICT")
    op.add_column("inventory_transactions", sa.Column("warehouse_id", psql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_inventory_transactions_warehouse_id", "inventory_transactions", "warehouses", ["warehouse_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "warehouse_inventory",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reorder_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_warehouse_inventory_quantity_nonnegative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_warehouse_inventory_reserved_nonnegative"),
        sa.CheckConstraint("reserved_quantity <= quantity", name="ck_warehouse_inventory_reserved_lte_quantity"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "warehouse_id", "product_id", name="uq_warehouse_inventory_org_wh_product"),
    )
    for name, columns in [("organization_id", ["organization_id"]), ("warehouse_id", ["warehouse_id"]), ("product_id", ["product_id"])]:
        op.create_index(f"ix_warehouse_inventory_{name}", "warehouse_inventory", columns)

    op.create_table(
        "inventory_transfers",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_warehouse_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination_warehouse_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT','REQUESTED','APPROVED','IN_TRANSIT','COMPLETED','CANCELLED')", name="ck_inventory_transfers_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_transfers_organization_id", "inventory_transfers", ["organization_id"])
    op.create_index("ix_inventory_transfers_status", "inventory_transfers", ["status"])

    op.create_table(
        "inventory_transfer_items",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["transfer_id"], ["inventory_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_id", "product_id", name="uq_inventory_transfer_product"),
    )

    op.create_table(
        "inventory_reservations",
        sa.Column("id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", psql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("reference_type", sa.String(80), nullable=True),
        sa.Column("reference_id", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", psql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_reservations_organization_id", "inventory_reservations", ["organization_id"])
    op.create_index("ix_inventory_reservations_status", "inventory_reservations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_inventory_reservations_status", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_organization_id", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")
    op.drop_table("inventory_transfer_items")
    op.drop_index("ix_inventory_transfers_status", table_name="inventory_transfers")
    op.drop_index("ix_inventory_transfers_organization_id", table_name="inventory_transfers")
    op.drop_table("inventory_transfers")
    for name in ("organization_id", "warehouse_id", "product_id"):
        op.drop_index(f"ix_warehouse_inventory_{name}", table_name="warehouse_inventory")
    op.drop_table("warehouse_inventory")
    op.drop_constraint("fk_inventory_transactions_warehouse_id", "inventory_transactions", type_="foreignkey")
    op.drop_column("inventory_transactions", "warehouse_id")
    op.drop_constraint("fk_purchase_orders_warehouse_id", "purchase_orders", type_="foreignkey")
    op.drop_column("purchase_orders", "warehouse_id")
    op.drop_index("ix_warehouses_branch_id", table_name="warehouses")
    op.drop_index("ix_warehouses_organization_id", table_name="warehouses")
    op.drop_table("warehouses")
