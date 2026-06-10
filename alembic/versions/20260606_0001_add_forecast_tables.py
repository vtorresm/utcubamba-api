"""add forecast_runs and forecast_points tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '3f4a2c5d6e7f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # forecast_runs
    op.create_table(
        'forecast_runs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('medication_id', sa.Integer(), sa.ForeignKey('medications.id'), nullable=False, index=True),
        sa.Column('model_type', sa.String(length=30), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('mae', sa.Float(), nullable=True),
        sa.Column('mape', sa.Float(), nullable=True),
        sa.Column('rmse', sa.Float(), nullable=True),
        sa.Column('r2', sa.Float(), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('stock_at_forecast', sa.Float(), nullable=True),
        sa.Column('days_until_shortage', sa.Integer(), nullable=True),
        sa.Column('shortage_probability', sa.Float(), nullable=True),
        sa.Column('alert_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # forecast_points
    op.create_table(
        'forecast_points',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('forecast_run_id', sa.Integer(), sa.ForeignKey('forecast_runs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('predicted_value', sa.Float(), nullable=False),
        sa.Column('lower_ci', sa.Float(), nullable=True),
        sa.Column('upper_ci', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('forecast_points')
    op.drop_table('forecast_runs')
