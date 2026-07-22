"""add waitlist table

Revision ID: f3a7c1e9b2d4
Revises: 8c12fa6cda54
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f3a7c1e9b2d4'
down_revision: Union[str, Sequence[str], None] = '8c12fa6cda54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'waitlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('map_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'notified', 'joined', name='waitlist_status'),
            server_default='pending',
            nullable=False,
        ),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['map_id'], ['maps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'map_id', name='uq_waitlist_user_map'),
    )
    op.create_index(op.f('ix_waitlist_user_id'), 'waitlist', ['user_id'], unique=False)
    op.create_index(op.f('ix_waitlist_map_id'), 'waitlist', ['map_id'], unique=False)
    op.create_index(op.f('ix_waitlist_status'), 'waitlist', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_waitlist_status'), table_name='waitlist')
    op.drop_index(op.f('ix_waitlist_map_id'), table_name='waitlist')
    op.drop_index(op.f('ix_waitlist_user_id'), table_name='waitlist')
    op.drop_table('waitlist')
