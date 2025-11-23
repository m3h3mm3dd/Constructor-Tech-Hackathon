"""add session based research tables

Revision ID: 20240401_sessions
Revises: 
Create Date: 2024-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240401_sessions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'research_sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('label', sa.String(), nullable=False, index=True),
        sa.Column('segment', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='PENDING'),
        sa.Column('max_companies', sa.Integer(), nullable=True),
        sa.Column('companies_found', sa.Integer(), nullable=False, default=0),
        sa.Column('charts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scoring_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'research_session_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('research_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('ts', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('level', sa.String(), default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        'session_companies',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('research_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('data_reliability', sa.String(), default='medium'),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('employees', sa.Integer(), nullable=True),
        sa.Column('hq_city', sa.String(), nullable=True),
        sa.Column('hq_country', sa.String(), nullable=True),
        sa.Column('primary_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'company_profiles',
        sa.Column('company_id', sa.String(), sa.ForeignKey('session_companies.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('score_analysis', sa.Text(), nullable=True),
        sa.Column('market_position', sa.Text(), nullable=True),
        sa.Column('background', sa.Text(), nullable=True),
        sa.Column('recent_developments', sa.Text(), nullable=True),
        sa.Column('products_services', sa.Text(), nullable=True),
        sa.Column('scale_reach', sa.Text(), nullable=True),
        sa.Column('strategic_notes', sa.Text(), nullable=True),
    )

    op.create_table(
        'company_sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('session_companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
    )

    op.create_table(
        'trend_analyses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('research_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('overview', sa.Text(), nullable=True),
        sa.Column('bars', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('trend_analyses')
    op.drop_table('company_sources')
    op.drop_table('company_profiles')
    op.drop_table('session_companies')
    op.drop_table('research_session_logs')
    op.drop_table('research_sessions')
