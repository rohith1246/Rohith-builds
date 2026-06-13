"""add google_id to user

Revision ID: 3fccdb63ac5a
Revises: 38e5aebcb7d5
Create Date: 2026-06-13 20:44:11.547413

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3fccdb63ac5a'
down_revision = '38e5aebcb7d5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_id', sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint('uq_user_google_id', ['google_id'])


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_google_id', type_='unique')
        batch_op.drop_column('google_id')
