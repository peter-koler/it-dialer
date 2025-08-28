"""merge multi-tenant and existing heads

Revision ID: ae128c8996b1
Revises: 0009_add_multi_tenant_support, 0009_merge_heads
Create Date: 2025-08-28 14:45:38.452991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae128c8996b1'
down_revision: Union[str, None] = ('0009_add_multi_tenant_support', '0009_merge_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
