"""add tenant-aware customer child foreign keys

Revision ID: e16f7a8b9c0d
Revises: d15e6f7a8b9c
"""

from alembic import op
import sqlalchemy as sa

revision = "e16f7a8b9c0d"
down_revision = "d15e6f7a8b9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    violations = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM customer_contacts cc
            JOIN customers c ON c.id = cc.customer_id
            WHERE c.organization_id <> cc.organization_id
            LIMIT 1
            """
        )
    ).first()
    if violations:
        raise RuntimeError("Cannot add customer tenant constraints: cross-organization contact data exists")
    violations = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM customer_addresses ca
            JOIN customers c ON c.id = ca.customer_id
            WHERE c.organization_id <> ca.organization_id
            LIMIT 1
            """
        )
    ).first()
    if violations:
        raise RuntimeError("Cannot add customer tenant constraints: cross-organization address data exists")

    op.create_unique_constraint(
        "uq_customers_organization_id_id", "customers", ["organization_id", "id"]
    )
    op.create_foreign_key(
        "fk_customer_contacts_org_customer",
        "customer_contacts",
        "customers",
        ["organization_id", "customer_id"],
        ["organization_id", "id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_customer_addresses_org_customer",
        "customer_addresses",
        "customers",
        ["organization_id", "customer_id"],
        ["organization_id", "id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_customer_addresses_org_customer", "customer_addresses", type_="foreignkey")
    op.drop_constraint("fk_customer_contacts_org_customer", "customer_contacts", type_="foreignkey")
    op.drop_constraint("uq_customers_organization_id_id", "customers", type_="unique")
