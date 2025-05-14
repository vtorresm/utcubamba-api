"""update_created_at

Revision ID: 20250513_1854
Revises: a364c67bdec9
Create Date: 2025-05-13 18:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '20250513_1854'
down_revision: Union[str, None] = 'a364c67bdec9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Primero actualizamos los valores null en users.created_at
    op.execute("""
        UPDATE users
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
    """)

    # Luego hacemos el campo NOT NULL
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)

    # Cambiamos el tipo de precio_unitario a Float
    op.alter_column('medicamentos', 'precio_unitario',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)

    # Actualizamos los valores null en alertas.fecha_creacion
    op.execute("""
        UPDATE alertas
        SET fecha_creacion = CURRENT_TIMESTAMP
        WHERE fecha_creacion IS NULL;
    """)

    # Luego hacemos el campo NOT NULL
    op.alter_column('alertas', 'fecha_creacion',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)

def downgrade() -> None:
    """Downgrade schema."""
    # Volver a permitir null en los campos
    op.alter_column('alertas', 'fecha_creacion',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)

    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)

    # Cambiar precio_unitario de Float a Integer
    op.alter_column('medicamentos', 'precio_unitario',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
