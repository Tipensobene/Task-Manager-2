"""create initial task tables

Revision ID: 042f491f9a4a
Revises:
Create Date: 2026-10-14 22:06:50.760768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '042f491f9a4a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tags",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.Text(),
            nullable=False,
            unique=True,
        ),

    )

    op.create_table(
        "tasks",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            primary_key=True,
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "done",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),

        sa.Column(
            "priority",
            sa.Text(),
            server_default=sa.text("'normal'"),
            nullable=False,
        )

    )

    op.create_table(
        "task_tags",
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id",
                          ondelete="CASCADE",
            ),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tags.id",
                          ondelete="CASCADE",
            ),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("task_tags")

    op.drop_table("tasks")
    op.drop_table("tags")
