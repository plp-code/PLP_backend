"""add performance indexes

Revision ID: 2f1d9d7d4e31
Revises: 189662e6c7ac
Create Date: 2026-06-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2f1d9d7d4e31"
down_revision: Union[str, Sequence[str], None] = "189662e6c7ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_user_map_access_user_id", "user_map_access", ["user_id"], unique=False)
    op.create_index("ix_user_map_access_map_id", "user_map_access", ["map_id"], unique=False)
    op.create_index("ix_user_map_access_map_user", "user_map_access", ["map_id", "user_id"], unique=False)
    op.create_index("ix_stores_map_id_id", "stores", ["map_id", "id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_stores_map_id_id", table_name="stores")
    op.drop_index("ix_user_map_access_map_user", table_name="user_map_access")
    op.drop_index("ix_user_map_access_map_id", table_name="user_map_access")
    op.drop_index("ix_user_map_access_user_id", table_name="user_map_access")
