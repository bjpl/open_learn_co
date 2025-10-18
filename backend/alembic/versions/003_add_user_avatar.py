"""Add avatar field to users table

Revision ID: 003_add_user_avatar
Revises: 002_add_performance_indexes
Create Date: 2025-01-17 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_user_avatar'
down_revision = '002_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add avatar column to users table"""
    # Add avatar URL column (stores either local path or cloud URL)
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

    # Add avatar metadata column for tracking upload info
    op.add_column('users', sa.Column('avatar_metadata', sa.JSON, nullable=True))

    # Add index for avatar queries (partial index for users with avatars)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_avatar
        ON users (avatar_url)
        WHERE avatar_url IS NOT NULL
    """)


def downgrade() -> None:
    """Remove avatar columns from users table"""
    op.drop_index('idx_users_avatar', table_name='users', if_exists=True)
    op.drop_column('users', 'avatar_metadata')
    op.drop_column('users', 'avatar_url')
