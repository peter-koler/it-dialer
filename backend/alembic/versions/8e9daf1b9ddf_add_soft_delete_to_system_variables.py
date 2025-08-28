"""add_soft_delete_to_system_variables

Revision ID: 8e9daf1b9ddf
Revises: ae128c8996b1
Create Date: 2025-08-28 16:32:35.560321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e9daf1b9ddf'
down_revision: Union[str, None] = 'ae128c8996b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为 system_variables 表添加软删除字段
    op.add_column('system_variables', sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False, comment='是否已删除'))
    op.add_column('system_variables', sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='删除时间'))
    
    # 创建索引以提高查询性能
    op.create_index('idx_system_variables_is_deleted', 'system_variables', ['is_deleted'])


def downgrade() -> None:
    # 删除软删除字段
    op.drop_index('idx_system_variables_is_deleted', 'system_variables')
    op.drop_column('system_variables', 'deleted_at')
    op.drop_column('system_variables', 'is_deleted')
