"""add supplier to products

Revision ID: 7a9b8c6d5e4f
Revises: 6a8b1c2d3e4f
Create Date: 2026-08-17 19:15:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = '7a9b8c6d5e4f'
down_revision = '6a8b1c2d3e4f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('products', sa.Column('supplier_id', psql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_products_supplier_id', 'products', 'suppliers', ['supplier_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_products_supplier_id', 'products', type_='foreignkey')
    op.drop_column('products', 'supplier_id')
