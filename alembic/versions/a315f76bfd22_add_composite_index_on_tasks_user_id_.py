"""add composite index on tasks user_id and created_at

Revision ID: a315f76bfd22
Revises: b40e2bbec768
Create Date: 2026-09-03 18:58:14.268100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a315f76bfd22'
down_revision: Union[str, Sequence[str], None] = 'b40e2bbec768'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_user_id_created_at",
        "tasks",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_user_id_created_at", table_name="tasks")
