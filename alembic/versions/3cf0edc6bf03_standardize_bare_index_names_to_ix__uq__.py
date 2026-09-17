"""standardize bare index names to ix_/uq_ convention

Revision ID: 3cf0edc6bf03
Revises: c8057b0a1ba7
Create Date: 2026-09-11 11:57:11.454687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cf0edc6bf03'
down_revision: Union[str, Sequence[str], None] = 'c8057b0a1ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE clothing_categories RENAME INDEX `name` TO uq_clothing_categories_name")
    op.execute("ALTER TABLE clothing_categories RENAME INDEX `slug` TO uq_clothing_categories_slug")

    op.execute("ALTER TABLE invoices RENAME INDEX stripe_checkout_session_id TO uq_invoices_stripe_checkout_session_id")
    op.execute("ALTER TABLE invoices RENAME INDEX stripe_payment_intent_id TO uq_invoices_stripe_payment_intent_id")
    op.execute("ALTER TABLE invoices RENAME INDEX map_id TO ix_invoices_map_id")

    op.execute("ALTER TABLE maps RENAME INDEX `name` TO uq_maps_name")
    op.execute("ALTER TABLE maps RENAME INDEX `slug` TO uq_maps_slug")

    op.execute("ALTER TABLE purchases RENAME INDEX invoice_id TO ix_purchases_invoice_id")
    op.execute("ALTER TABLE purchases RENAME INDEX map_id TO ix_purchases_map_id")

    op.execute("ALTER TABLE review_categories RENAME INDEX category_id TO ix_review_categories_category_id")

    op.execute("ALTER TABLE tokens RENAME INDEX token TO uq_tokens_token")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE tokens RENAME INDEX uq_tokens_token TO token")
   
    op.execute("ALTER TABLE review_categories RENAME INDEX ix_review_categories_category_id TO category_id")

    op.execute("ALTER TABLE purchases RENAME INDEX ix_purchases_map_id TO map_id")
    op.execute("ALTER TABLE purchases RENAME INDEX ix_purchases_invoice_id TO invoice_id")

    op.execute("ALTER TABLE maps RENAME INDEX uq_maps_slug TO `slug`")
    op.execute("ALTER TABLE maps RENAME INDEX uq_maps_name TO `name`")

    op.execute("ALTER TABLE invoices RENAME INDEX ix_invoices_map_id TO map_id")
    op.execute("ALTER TABLE invoices RENAME INDEX uq_invoices_stripe_payment_intent_id TO stripe_payment_intent_id")
    op.execute("ALTER TABLE invoices RENAME INDEX uq_invoices_stripe_checkout_session_id TO stripe_checkout_session_id")

    op.execute("ALTER TABLE clothing_categories RENAME INDEX uq_clothing_categories_slug TO `slug`")
    op.execute("ALTER TABLE clothing_categories RENAME INDEX uq_clothing_categories_name TO `name`")