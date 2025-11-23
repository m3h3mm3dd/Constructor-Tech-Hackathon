"""create legacy companies table

Revision ID: 20240402_legacy_companies
Revises: 20240401_sessions
Create Date: 2024-04-02
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240402_legacy_companies'
down_revision = '20240401_sessions'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('segment', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('size_bucket', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('background', sa.Text(), nullable=True),
        sa.Column('products', sa.Text(), nullable=True),
        sa.Column('target_segments', sa.Text(), nullable=True),
        sa.Column('pricing_model', sa.Text(), nullable=True),
        sa.Column('market_position', sa.Text(), nullable=True),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('risks', sa.Text(), nullable=True),
        sa.Column('has_ai_features', sa.Boolean(), default=False),
        sa.Column('compliance_tags', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('first_discovered', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'source_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'research_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('segment', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_table('research_jobs')
    op.drop_table('source_documents')
    op.drop_table('companies')
