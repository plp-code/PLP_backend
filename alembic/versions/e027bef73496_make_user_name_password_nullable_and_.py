"""make user name/password nullable and add role column

Revision ID: e027bef73496
Revises: 1981361768d4
Create Date: 2026-09-28 18:34:51.712115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e027bef73496'
down_revision: Union[str, Sequence[str], None] = '1981361768d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users", "hashed_password",
        existing_type=sa.String(255),
        nullable=True,
    )
    op.alter_column(
        "users", "first_name",
        existing_type=sa.String(255),
        nullable=True,
    )
    op.alter_column(
        "users", "last_name",
        existing_type=sa.String(255),
        nullable=True,
    )

    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_check_constraint(
        "ck_users_role", "users", "role IN ('user', 'admin')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "role")

    op.alter_column(
        "users", "last_name",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.alter_column(
        "users", "first_name",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.alter_column(
        "users", "hashed_password",
        existing_type=sa.String(255),
        nullable=False,
    )