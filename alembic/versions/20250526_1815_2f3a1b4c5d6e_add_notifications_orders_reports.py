"""Add notifications, orders, reports tables

Revision ID: 2f3a1b4c5d6e
Revises: 46cbc28d0e6b
Create Date: 2025-05-26 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '2f3a1b4c5d6e'
down_revision: Union[str, None] = '46cbc28d0e6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### notifications table ###
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.String(length=2000), nullable=False),
        sa.Column('type', sa.Enum('SHORTAGE_ALERT', 'STOCK_ALERT', 'ORDER_UPDATE', 'SYSTEM', 'INFO', name='notificationtype'), nullable=False),
        sa.Column('level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='notificationlevel'), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('related_entity_type', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ### orders table ###
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'SHIPPED', 'RECEIVED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('received_date', sa.DateTime(), nullable=True),
        sa.Column('supplier', sa.String(length=200), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ### reports table ###
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('type', sa.Enum('INVENTORY', 'MOVEMENTS', 'TRENDS', 'ALERTS', 'FINANCIAL', 'PATIENTS', name='reporttype'), nullable=False),
        sa.Column('format', sa.Enum('PDF', 'EXCEL', 'CSV', name='reportformat'), nullable=False),
        sa.Column('status', sa.Enum('GENERATING', 'COMPLETED', 'FAILED', name='reportstatus'), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('generated_by', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('orders')
    op.drop_table('notifications')

    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS notificationlevel")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS reporttype")
    op.execute("DROP TYPE IF EXISTS reportformat")
    op.execute("DROP TYPE IF EXISTS reportstatus")
