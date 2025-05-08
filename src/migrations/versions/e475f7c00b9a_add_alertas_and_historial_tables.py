"""add_alertas_and_historial_tables

Revision ID: e475f7c00b9a
Revises: 61d2ab4dfa58
Create Date: 2025-05-08 17:22:15.457771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e475f7c00b9a'
down_revision: Union[str, None] = '61d2ab4dfa58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
