"""Initial migration

Revision ID: 46cbc28d0e6b
Revises: 
Create Date: 2025-05-20 11:43:32.536928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '46cbc28d0e6b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)
    op.create_table('conditions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conditions_name'), 'conditions', ['name'], unique=True)
    op.create_table('intake_types',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intake_types_name'), 'intake_types', ['name'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('cargo', sa.String(length=100), nullable=False),
    sa.Column('departamento', sa.String(length=100), nullable=False),
    sa.Column('contacto', sa.String(length=50), nullable=True),
    sa.Column('fecha_ingreso', sa.DateTime(), nullable=False),
    sa.Column('estado', sa.Enum('ACTIVO', 'DADO_DE_BAJA', name='userstatus'), nullable=False),
    sa.Column('role', sa.Enum('ADMIN', 'USER', 'FARMACIA', 'ENFERMERIA', name='role'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('medications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('stock', sa.Integer(), nullable=False),
    sa.Column('min_stock', sa.Integer(), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('intake_type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['intake_type_id'], ['intake_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medications_name'), 'medications', ['name'], unique=False)
    op.create_table('password_reset_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('medication_condition',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('medication_id', sa.Integer(), nullable=False),
    sa.Column('condition_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['condition_id'], ['conditions.id'], ),
    sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
    sa.PrimaryKeyConstraint('id', 'medication_id', 'condition_id')
    )
    op.create_table('movements',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('type', sa.Enum('IN', 'OUT', name='movementtype'), nullable=False),
    sa.Column('quantity', sa.Float(), nullable=False),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('medication_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('predictions',
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('real_usage', sa.Float(), nullable=False),
    sa.Column('predicted_usage', sa.Float(), nullable=False),
    sa.Column('stock', sa.Float(), nullable=False),
    sa.Column('month_of_year', sa.Integer(), nullable=False),
    sa.Column('regional_demand', sa.Float(), nullable=False),
    sa.Column('restock_time', sa.Float(), nullable=True),
    sa.Column('shortage', sa.Boolean(), nullable=False),
    sa.Column('probability', sa.Float(), nullable=True),
    sa.Column('medication_id', sa.Integer(), nullable=False),
    sa.Column('movement_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
    sa.ForeignKeyConstraint(['movement_id'], ['movements.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('predictions')
    op.drop_table('movements')
    op.drop_table('medication_condition')
    op.drop_table('password_reset_tokens')
    op.drop_index(op.f('ix_medications_name'), table_name='medications')
    op.drop_table('medications')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_intake_types_name'), table_name='intake_types')
    op.drop_table('intake_types')
    op.drop_index(op.f('ix_conditions_name'), table_name='conditions')
    op.drop_table('conditions')
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_table('categories')
    # ### end Alembic commands ###
