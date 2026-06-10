"""Add missing fields to medications table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-06 00:01:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columnas faltantes en medications
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('medications')]

    if 'manufacturer' not in existing_cols:
        op.add_column('medications', sa.Column('manufacturer', sa.String(length=200), nullable=True))

    if 'expiration_date' not in existing_cols:
        op.add_column('medications', sa.Column('expiration_date', sa.DateTime(), nullable=True))

    if 'status' not in existing_cols:
        op.add_column('medications', sa.Column('status', sa.String(length=50), nullable=False, server_default='Activo'))

    if 'price' not in existing_cols:
        op.add_column('medications', sa.Column('price', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('medications', 'price')
    op.drop_column('medications', 'status')
    op.drop_column('medications', 'expiration_date')
    op.drop_column('medications', 'manufacturer')
