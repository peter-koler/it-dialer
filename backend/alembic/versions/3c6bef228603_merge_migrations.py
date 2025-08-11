"""merge migrations

Revision ID: 3c6bef228603
Revises: 0003_add_agent_ids_to_tasks, 144610be5f76
Create Date: 2025-08-10 21:40:49.541464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c6bef228603'
down_revision: Union[str, None] = ('0003_add_agent_ids_to_tasks', '144610be5f76')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass