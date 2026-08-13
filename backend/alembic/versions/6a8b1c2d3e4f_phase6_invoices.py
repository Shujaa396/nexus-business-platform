"""phase6 invoices tables

Revision ID: 6a8b1c2d3e4f
Revises: 5f7e9c1d2a3b
Create Date: 2026-08-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = '6a8b1c2d3e4f'
down_revision = '5f7e9c1d2a3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'invoices',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_number', sa.String(64), nullable=False),
        sa.Column('order_number', sa.String(64), nullable=False),
        sa.Column('branch_name', sa.String(255), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('customer_email', sa.String(255), nullable=True),
        sa.Column('customer_phone', sa.String(50), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='DRAFT'),
        sa.Column('issued_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subtotal', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('discount', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('tax', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('total', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('amount_paid', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('issued_by', psql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['issued_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'invoice_number', name='uq_invoices_org_invoice_number'),
        sa.UniqueConstraint('organization_id', 'order_id', name='uq_invoices_org_order'),
        sa.CheckConstraint("status IN ('DRAFT', 'ISSUED', 'PARTIAL', 'PAID', 'VOID')", name='ck_invoices_status'),
    )
    op.create_index('ix_invoices_organization_id', 'invoices', ['organization_id'])
    op.create_index('ix_invoices_branch_id', 'invoices', ['branch_id'])
    op.create_index('ix_invoices_customer_id', 'invoices', ['customer_id'])
    op.create_index('ix_invoices_order_id', 'invoices', ['order_id'])
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'])

    op.create_table(
        'invoice_line_items',
        sa.Column('id', psql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_item_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', psql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_sku', sa.String(120), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('discount', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('tax', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(18, 4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
    )
    op.create_index('ix_invoice_line_items_organization_id', 'invoice_line_items', ['organization_id'])
    op.create_index('ix_invoice_line_items_invoice_id', 'invoice_line_items', ['invoice_id'])
    op.create_index('ix_invoice_line_items_order_item_id', 'invoice_line_items', ['order_item_id'])
    op.create_index('ix_invoice_line_items_product_id', 'invoice_line_items', ['product_id'])


def downgrade() -> None:
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
