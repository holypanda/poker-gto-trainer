"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('total_trains', sa.Integer(), nullable=True),
        sa.Column('correct_trains', sa.Integer(), nullable=True),
        sa.Column('streak_days', sa.Integer(), nullable=True),
        sa.Column('last_train_date', sa.DateTime(), nullable=True),
        sa.Column('is_subscribed', sa.Boolean(), nullable=True),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('free_trains_today', sa.Integer(), nullable=True),
        sa.Column('free_trains_reset_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Create training_sessions table
    op.create_table(
        'training_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stack_size', sa.Integer(), nullable=False),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('action_to_you', sa.String(), nullable=False),
        sa.Column('scenarios', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('current_index', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_sessions_id', 'training_sessions', ['id'], unique=False)

    # Create training_records table
    op.create_table(
        'training_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hand', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=False),
        sa.Column('vs_position', sa.String(), nullable=True),
        sa.Column('action_to_you', sa.String(), nullable=False),
        sa.Column('correct_action', sa.String(), nullable=False),
        sa.Column('gto_frequency', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('user_action', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['training_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_records_id', 'training_records', ['id'], unique=False)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('alipay_trade_no', sa.String(), nullable=True),
        sa.Column('alipay_buyer_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subscriptions_id', 'subscriptions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index('ix_training_records_id', table_name='training_records')
    op.drop_table('training_records')
    op.drop_index('ix_training_sessions_id', table_name='training_sessions')
    op.drop_table('training_sessions')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
