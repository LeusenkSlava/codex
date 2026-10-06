"""Add kind to tag

Revision ID: 3f8b6a1c9d2e
Revises: 54fbe6ddff24
Create Date: 2026-10-06 14:23:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3f8b6a1c9d2e'
down_revision: Union[str, Sequence[str], None] = '54fbe6ddff24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    tagkind = postgresql.ENUM('base_emotion', 'modifier', name='tagkind')
    tagkind.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'tags',
        sa.Column(
            'kind',
            postgresql.ENUM('base_emotion', 'modifier', name='tagkind'),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tags', 'kind')
    postgresql.ENUM(name='tagkind').drop(op.get_bind(), checkfirst=True)
