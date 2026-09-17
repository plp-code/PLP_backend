"""add timestamps, unique constraints, and check constraints for data integrity

Revision ID: c8057b0a1ba7
Revises: f29bb3ab56c4
Create Date: 2026-09-11 11:37:28.858154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'c8057b0a1ba7'
down_revision: Union[str, Sequence[str], None] = 'f29bb3ab56c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('invoices', 'currency',
               existing_type=mysql.VARCHAR(length=10),
               type_=sa.String(length=3),
               existing_nullable=False)

    op.create_unique_constraint('uq_locations_google_place_id', 'locations', ['google_place_id'])

    op.add_column('purchases', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('purchases', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('tokens', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))

    # CHECK constraints — autogenerate doesn't reliably detect these, added manually
    op.create_check_constraint(
        'chk_location_hours_day_of_week',
        'location_hours',
        'day_of_week BETWEEN 0 AND 6'
    )
    op.create_check_constraint(
        'chk_locations_price_range',
        'locations',
        'min_price IS NULL OR max_price IS NULL OR min_price <= max_price'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('chk_locations_price_range', 'locations', type_='check')
    op.drop_constraint('chk_location_hours_day_of_week', 'location_hours', type_='check')

    op.drop_column('tokens', 'updated_at')
    op.drop_column('purchases', 'updated_at')
    op.drop_column('purchases', 'created_at')

    op.drop_constraint('uq_locations_google_place_id', 'locations', type_='unique')

    op.alter_column('invoices', 'currency',
               existing_type=sa.String(length=3),
               type_=mysql.VARCHAR(length=10),
               existing_nullable=False)