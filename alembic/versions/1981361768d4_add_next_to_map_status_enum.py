"""add_next_to_map_status_enum

Revision ID: 1981361768d4
Revises: 3cf0edc6bf03
Create Date: 2026-09-17 16:34:08.435408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1981361768d4'
down_revision: Union[str, Sequence[str], None] = '3cf0edc6bf03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("SET lock_wait_timeout = 5;")
    op.execute("""
        ALTER TABLE maps
        MODIFY COLUMN status ENUM('live', 'waitlist', 'dropped', 'next')
        NOT NULL
        DEFAULT 'waitlist',
        ALGORITHM=INSTANT;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("SET lock_wait_timeout = 5;")
    op.execute("""
        UPDATE maps
        SET status = 'waitlist'
        WHERE status = 'next';
    """)
    op.execute("""
        ALTER TABLE maps
        MODIFY COLUMN status ENUM('live', 'waitlist', 'dropped')
        NOT NULL
        DEFAULT 'waitlist';
    """)