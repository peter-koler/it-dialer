"""merge_heads_and_add_trigger_fields

Revision ID: 840c1438c4b7
Revises: 0010_add_enhanced_alert_config_fields, 8e9daf1b9ddf
Create Date: 2025-08-31 22:04:10.634193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '840c1438c4b7'
down_revision: Union[str, None] = ('0010_add_enhanced_alert_config_fields', '8e9daf1b9ddf')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
