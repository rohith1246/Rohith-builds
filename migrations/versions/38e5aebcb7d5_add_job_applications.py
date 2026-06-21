"""add job_applications

Revision ID: 38e5aebcb7d5
Revises: 
Create Date: 2026-06-13 15:57:09.844511

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '38e5aebcb7d5'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Safely create job_applications table only if it does not exist yet
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if 'job_applications' not in tables:
        op.create_table('job_applications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=False),
            sa.Column('applied_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'job_id', name='uq_user_job_application')
        )


def downgrade():
    op.drop_table('job_applications')
