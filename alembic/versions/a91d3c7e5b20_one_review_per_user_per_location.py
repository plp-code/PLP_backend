"""one review per user per location

Revision ID: a91d3c7e5b20
Revises: c437f101fbbb
Create Date: 2026-11-24 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a91d3c7e5b20'
down_revision: Union[str, Sequence[str], None] = 'c437f101fbbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fails if duplicate (user_id, location_id) rows already exist; resolve those first:
    #   SELECT user_id, location_id, COUNT(*) FROM reviews GROUP BY 1, 2 HAVING COUNT(*) > 1;
    op.create_unique_constraint('uq_reviews_user_location', 'reviews', ['user_id', 'location_id'])


def downgrade() -> None:
    op.drop_constraint('uq_reviews_user_location', 'reviews', type_='unique')
