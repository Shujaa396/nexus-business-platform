"""phase4 inventory tables

Revision ID: 3b5f9b6a9f3c
Revises: d3f75c9a624f
Create Date: 2026-08-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = '3b5f9b6a9f3c'
down_revision = 'd3f75c9a624f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inventory_items',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('reorder_level', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('organization_id', 'branch_id', 'product_id', name='uq_inventory_org_branch_product'),
    )
    op.create_index('ix_inventory_items_organization_id', 'inventory_items', ['organization_id'])
    op.create_index('ix_inventory_items_branch_id', 'inventory_items', ['branch_id'])
    op.create_index('ix_inventory_items_product_id', 'inventory_items', ['product_id'])

    op.create_table(
        'inventory_transactions',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('inventory_item_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(18,4), nullable=False),
        sa.Column('reference_type', sa.String(120), nullable=True),
        sa.Column('reference_id', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['inventory_item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_inventory_tx_organization_id', 'inventory_transactions', ['organization_id'])
    op.create_index('ix_inventory_tx_branch_id', 'inventory_transactions', ['branch_id'])
    op.create_index('ix_inventory_tx_product_id', 'inventory_transactions', ['product_id'])
    op.create_index('ix_inventory_tx_created_at', 'inventory_transactions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_inventory_tx_created_at', table_name='inventory_transactions')
    op.drop_index('ix_inventory_tx_product_id', table_name='inventory_transactions')
    op.drop_index('ix_inventory_tx_branch_id', table_name='inventory_transactions')
    op.drop_index('ix_inventory_tx_organization_id', table_name='inventory_transactions')
    op.drop_table('inventory_transactions')

    op.drop_index('ix_inventory_items_product_id', table_name='inventory_items')
    op.drop_index('ix_inventory_items_branch_id', table_name='inventory_items')
    op.drop_index('ix_inventory_items_organization_id', table_name='inventory_items')
    op.drop_table('inventory_items')
