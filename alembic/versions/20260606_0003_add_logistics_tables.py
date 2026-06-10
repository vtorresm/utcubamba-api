"""add suppliers, lots, lot_events, audits, deliveries tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # suppliers
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('contact_name', sa.String(length=150), nullable=True),
        sa.Column('contact_email', sa.String(length=150), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # lots
    op.create_table(
        'lots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(length=50), nullable=False, index=True),
        sa.Column('medication_id', sa.Integer(), sa.ForeignKey('medications.id'), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('location', sa.String(length=150), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('manufactured_date', sa.Date(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='received'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # lot_events
    op.create_table(
        'lot_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lot_id', sa.Integer(), sa.ForeignKey('lots.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('detail', sa.String(length=500), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('step_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # audits
    op.create_table(
        'audits',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('sector', sa.String(length=150), nullable=False),
        sa.Column('audit_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('documentation_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('precision_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('responsible_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # deliveries
    op.create_table(
        'deliveries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False, index=True),
        sa.Column('medication_id', sa.Integer(), sa.ForeignKey('medications.id'), nullable=True, index=True),
        sa.Column('product', sa.String(length=250), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_transit'),
        sa.Column('eta', sa.DateTime(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('deliveries')
    op.drop_table('audits')
    op.drop_table('lot_events')
    op.drop_table('lots')
    op.drop_table('suppliers')
