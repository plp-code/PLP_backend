"""add google_place_id to locations

Revision ID: bd1e7cfaa3cd
Revises: b95e49bef0e4
Create Date: 2026-06-28 00:11:41.075805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'bd1e7cfaa3cd'
down_revision: Union[str, Sequence[str], None] = 'b95e49bef0e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('maps', sa.Column('google_place_id', sa.String(length=255), nullable=True))
    op.alter_column('tokens', 'is_revoked',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True,
               existing_server_default=sa.text("'0'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('tokens', 'is_revoked',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False,
               existing_server_default=sa.text("'0'"))
    op.drop_column('maps', 'google_place_id')
