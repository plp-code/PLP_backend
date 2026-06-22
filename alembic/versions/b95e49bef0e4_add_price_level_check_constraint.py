"""add price_level check constraint

Revision ID: b95e49bef0e4
Revises: 23d9ac9812eb
Create Date: 2026-06-21 22:50:19.309921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b95e49bef0e4'
down_revision: Union[str, Sequence[str], None] = '23d9ac9812eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restrict locations.price_level to the PriceLevel enum values (1, 2, 3)."""
    op.create_check_constraint(
        "chk_locations_price_level", "locations", "price_level IN (1, 2, 3)"
    )


def downgrade() -> None:
    """Drop the price_level check constraint."""
    op.drop_constraint("chk_locations_price_level", "locations", type_="check")
