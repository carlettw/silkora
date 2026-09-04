"""add route_points to tours
 
Revision ID: a1b2c3d4e5f6
Revises: 465368d9dd59
Create Date: 2026-09-02 00:00:00.000000
 
"""
from typing import Sequence, Union
 
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
 
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '465368d9dd59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
 
 
def upgrade() -> None:
    op.add_column('tours', sa.Column('route_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
 
 
def downgrade() -> None:
    op.drop_column('tours', 'route_points')
 
