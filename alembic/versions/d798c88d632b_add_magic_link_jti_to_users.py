"""add magic_link_jti to users

Revision ID: d798c88d632b
Revises: e027bef73496
Create Date: 2026-09-28 19:04:16.696127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd798c88d632b'
down_revision: Union[str, Sequence[str], None] = 'e027bef73496'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("magic_link_jti", sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "magic_link_jti")
