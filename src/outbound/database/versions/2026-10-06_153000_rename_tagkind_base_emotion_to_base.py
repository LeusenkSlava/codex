"""Rename tagkind value base_emotion to base

Revision ID: 7c2d9e4f5a1b
Revises: 3f8b6a1c9d2e
Create Date: 2026-10-06 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7c2d9e4f5a1b'
down_revision: Union[str, Sequence[str], None] = '3f8b6a1c9d2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tagkind RENAME VALUE 'base_emotion' TO 'base'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE tagkind RENAME VALUE 'base' TO 'base_emotion'")
