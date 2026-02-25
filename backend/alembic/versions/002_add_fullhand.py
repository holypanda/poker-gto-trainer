"""add fullhand tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 创建完整牌局会话表
    op.create_table(
        'fullhand_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('table_type', sa.String(), nullable=True),
        sa.Column('stack_bb', sa.Integer(), nullable=True),
        sa.Column('ai_level', sa.String(), nullable=True),
        sa.Column('hand_seed', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('current_street', sa.String(), nullable=True),
        sa.Column('players', sa.JSON(), nullable=True),
        sa.Column('button_seat', sa.Integer(), nullable=True),
        sa.Column('sb_seat', sa.Integer(), nullable=True),
        sa.Column('bb_seat', sa.Integer(), nullable=True),
        sa.Column('pot', sa.Float(), nullable=True),
        sa.Column('current_bet', sa.Float(), nullable=True),
        sa.Column('community_cards', sa.JSON(), nullable=True),
        sa.Column('action_log', sa.JSON(), nullable=True),
        sa.Column('hero_seat', sa.Integer(), nullable=True),
        sa.Column('hero_cards', sa.JSON(), nullable=True),
        sa.Column('preflop_key_spot', sa.JSON(), nullable=True),
        sa.Column('flop_key_spot', sa.JSON(), nullable=True),
        sa.Column('result_bb', sa.Float(), nullable=True),
        sa.Column('ended_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fullhand_sessions_id'), 'fullhand_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_fullhand_sessions_user_id'), 'fullhand_sessions', ['user_id'], unique=False)
    
    # 创建统计表
    op.create_table(
        'fullhand_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_hands', sa.Integer(), nullable=True),
        sa.Column('preflop_key_spots', sa.Integer(), nullable=True),
        sa.Column('flop_key_spots', sa.Integer(), nullable=True),
        sa.Column('preflop_correct', sa.Integer(), nullable=True),
        sa.Column('preflop_total', sa.Integer(), nullable=True),
        sa.Column('flop_correct', sa.Integer(), nullable=True),
        sa.Column('flop_total', sa.Integer(), nullable=True),
        sa.Column('total_result_bb', sa.Float(), nullable=True),
        sa.Column('total_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fullhand_stats_date'), 'fullhand_stats', ['date'], unique=False)
    op.create_index(op.f('ix_fullhand_stats_id'), 'fullhand_stats', ['id'], unique=False)
    op.create_index(op.f('ix_fullhand_stats_user_id'), 'fullhand_stats', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_fullhand_stats_user_id'), table_name='fullhand_stats')
    op.drop_index(op.f('ix_fullhand_stats_id'), table_name='fullhand_stats')
    op.drop_index(op.f('ix_fullhand_stats_date'), table_name='fullhand_stats')
    op.drop_table('fullhand_stats')
    
    op.drop_index(op.f('ix_fullhand_sessions_user_id'), table_name='fullhand_sessions')
    op.drop_index(op.f('ix_fullhand_sessions_id'), table_name='fullhand_sessions')
    op.drop_table('fullhand_sessions')
