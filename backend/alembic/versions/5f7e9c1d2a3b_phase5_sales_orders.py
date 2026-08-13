"""phase5 sales and orders tables

Revision ID: 5f7e9c1d2a3b
Revises: 4c6d8a7b2e1f
Create Date: 2026-08-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = '5f7e9c1d2a3b'
down_revision = '4c6d8a7b2e1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_number', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='DRAFT'),
        sa.Column('payment_status', sa.String(32), nullable=False, server_default='UNPAID'),
        sa.Column('subtotal', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('discount', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('tax', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'order_number', name='uq_orders_org_order_number'),
    )
    op.create_index('ix_orders_organization_id', 'orders', ['organization_id'])
    op.create_index('ix_orders_branch_id', 'orders', ['branch_id'])
    op.create_index('ix_orders_order_number', 'orders', ['order_number'])

    op.create_table(
        'order_items',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('order_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Numeric(18,4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18,4), nullable=False),
        sa.Column('discount', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('tax', sa.Numeric(18,4), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(18,4), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'])

    op.create_table(
        'payments',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(18,4), nullable=False),
        sa.Column('payment_method', sa.String(32), nullable=False),
        sa.Column('reference', sa.String(255), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_payments_organization_id', 'payments', ['organization_id'])
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])

    op.create_table(
        'order_status_history',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_status', sa.String(32), nullable=False),
        sa.Column('new_status', sa.String(32), nullable=False),
        sa.Column('changed_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_order_status_history_order_id', 'order_status_history', ['order_id'])


def downgrade() -> None:
    op.drop_index('ix_order_status_history_order_id', table_name='order_status_history')
    op.drop_table('order_status_history')

    op.drop_index('ix_payments_order_id', table_name='payments')
    op.drop_index('ix_payments_organization_id', table_name='payments')
    op.drop_table('payments')

    op.drop_index('ix_order_items_product_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')

    op.drop_index('ix_orders_order_number', table_name='orders')
    op.drop_index('ix_orders_branch_id', table_name='orders')
    op.drop_index('ix_orders_organization_id', table_name='orders')
    op.drop_table('orders')
