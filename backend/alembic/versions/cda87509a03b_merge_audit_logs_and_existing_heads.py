"""merge audit logs and existing heads

Revision ID: cda87509a03b
Revises: 0012_add_audit_logs_table, 840c1438c4b7
Create Date: 2025-09-02 18:48:13.679703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cda87509a03b'
down_revision: Union[str, None] = ('0012_add_audit_logs_table', '840c1438c4b7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
