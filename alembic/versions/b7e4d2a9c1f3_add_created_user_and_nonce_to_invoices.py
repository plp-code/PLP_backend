"""add created_user and checkout_nonce_hash to invoices

Revision ID: b7e4d2a9c1f3
Revises: 03664f50b050
Create Date: 2026-11-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e4d2a9c1f3'
down_revision: Union[str, Sequence[str], None] = '03664f50b050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Existing invoices get created_user = false, so no pre-existing guest
    invoice can ever mint a session after this deploy.
    """
    op.add_column(
        'invoices',
        sa.Column('created_user', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'invoices',
        sa.Column('checkout_nonce_hash', sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('invoices', 'checkout_nonce_hash')
    op.drop_column('invoices', 'created_user')
