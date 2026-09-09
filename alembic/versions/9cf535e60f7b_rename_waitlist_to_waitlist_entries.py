"""rename waitlist to waitlist_entries

Revision ID: 9cf535e60f7b
Revises: 0fddcf6d5ccb
Create Date: 2026-09-09 18:03:57.945105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9cf535e60f7b'
down_revision: Union[str, Sequence[str], None] = '0fddcf6d5ccb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table('waitlist', 'waitlist_entries')

    # Rename indexes to match new table name
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_map_id TO ix_waitlist_entries_map_id")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_status TO ix_waitlist_entries_status")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_user_id TO ix_waitlist_entries_user_id")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX uq_waitlist_user_map TO uq_waitlist_entries_user_map")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_entries_map_id TO ix_waitlist_map_id")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_entries_status TO ix_waitlist_status")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX ix_waitlist_entries_user_id TO ix_waitlist_user_id")
    op.execute("ALTER TABLE waitlist_entries RENAME INDEX uq_waitlist_entries_user_map TO uq_waitlist_user_map")

    op.rename_table('waitlist_entries', 'waitlist')