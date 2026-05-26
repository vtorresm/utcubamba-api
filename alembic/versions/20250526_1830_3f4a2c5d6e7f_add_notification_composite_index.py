"""Add composite index on notifications (user_id, read, created_at)

Revision ID: 3f4a2c5d6e7f
Revises: 2f3a1b4c5d6e
Create Date: 2025-05-26 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f4a2c5d6e7f'
down_revision: Union[str, None] = '2f3a1b4c5d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_notifications_user_read_created',
        'notifications',
        ['user_id', 'read', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_user_read_created', table_name='notifications')
