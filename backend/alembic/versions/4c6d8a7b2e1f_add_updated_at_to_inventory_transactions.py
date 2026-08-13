"""add updated_at to inventory_transactions

Revision ID: 4c6d8a7b2e1f
Revises: 3b5f9b6a9f3c
Create Date: 2026-08-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4c6d8a7b2e1f'
down_revision = '3b5f9b6a9f3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'inventory_transactions',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
    )


def downgrade() -> None:
    op.drop_column('inventory_transactions', 'updated_at')
