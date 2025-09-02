"""add max_users field and unique constraint for multi-tenant

Revision ID: 0011_add_max_users_and_unique_constraint
Revises: 0010_add_enhanced_alert_config_fields
Create Date: 2025-01-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0011_add_max_users_and_unique_constraint'
down_revision: Union[str, None] = '0010_add_enhanced_alert_config_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为 tenants 表添加 max_users 字段
    op.add_column('tenants', sa.Column('max_users', sa.Integer(), nullable=False, default=15, comment='用户数量上限'))
    
    # 添加 CHECK 约束确保 max_users >= 1
    op.create_check_constraint(
        'ck_tenants_max_users_positive',
        'tenants',
        'max_users >= 1'
    )
    
    # 为 user_tenants 表添加 unique(user_id) 约束，确保用户只能属于一个租户
    op.create_unique_constraint('uq_user_tenants_user_id', 'user_tenants', ['user_id'])
    
    # 添加必要的索引
    op.create_index('idx_tenants_name', 'tenants', ['name'])
    op.create_index('idx_user_tenants_tenant_id', 'user_tenants', ['tenant_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_user_tenants_tenant_id', 'user_tenants')
    op.drop_index('idx_tenants_name', 'tenants')
    
    # 删除 unique 约束
    op.drop_constraint('uq_user_tenants_user_id', 'user_tenants', type_='unique')
    
    # 删除 CHECK 约束
    op.drop_constraint('ck_tenants_max_users_positive', 'tenants', type_='check')
    
    # 删除 max_users 字段
    op.drop_column('tenants', 'max_users')