"""add multi-tenant support

Revision ID: 0009
Revises: 0008
Create Date: 2025-01-21 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import uuid

# revision identifiers, used by Alembic.
revision: str = '0009_add_multi_tenant_support'
down_revision: Union[str, None] = '0008_add_reports_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 创建租户表 ###
    op.create_table('tenants',
        sa.Column('id', sa.String(36), nullable=False, comment='租户ID (UUID)'),
        sa.Column('name', sa.String(100), nullable=False, comment='租户名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='租户描述'),
        sa.Column('subscription_level', sa.Enum('free', 'pro', 'enterprise', name='subscription_level_enum'), nullable=False, default='free', comment='订阅级别'),
        sa.Column('max_tasks', sa.Integer(), nullable=False, default=10, comment='任务数量上限'),
        sa.Column('max_nodes', sa.Integer(), nullable=False, default=5, comment='节点数量上限'),
        sa.Column('max_variables', sa.Integer(), nullable=False, default=20, comment='变量数量上限'),
        sa.Column('max_alerts', sa.Integer(), nullable=False, default=10, comment='告警规则上限'),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', name='tenant_status_enum'), nullable=False, default='active', comment='租户状态'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('meta_data', sa.JSON(), nullable=True, comment='扩展字段'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 创建租户表索引
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    op.create_index('idx_tenants_subscription', 'tenants', ['subscription_level'])
    
    # ### 创建用户-租户关联表 ###
    op.create_table('user_tenants',
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('tenant_id', sa.String(36), nullable=False, comment='租户ID'),
        sa.Column('role', sa.Enum('user', 'tenant_admin', 'super_admin', name='user_tenant_role_enum'), nullable=False, default='user', comment='用户在租户中的角色'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.PrimaryKeyConstraint('user_id', 'tenant_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )
    
    # 创建用户-租户关联表索引
    op.create_index('idx_user_tenants_tenant_role', 'user_tenants', ['tenant_id', 'role'])
    
    # ### 为现有表添加 tenant_id 字段 ###
    
    # 为 tasks 表添加 tenant_id
    op.add_column('tasks', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_tasks_tenant_id', 'tasks', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_tasks_tenant', 'tasks', ['tenant_id', 'status', 'created_at'])
    
    # 为 results 表添加 tenant_id
    op.add_column('results', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_results_tenant_id', 'results', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_results_tenant', 'results', ['tenant_id', 'task_id', 'created_at'])
    
    # 为 nodes 表添加 tenant_id
    op.add_column('nodes', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_nodes_tenant_id', 'nodes', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_nodes_tenant', 'nodes', ['tenant_id', 'status'])
    
    # 为 system_variables 表添加 tenant_id (可为空，$public_ 变量)
    op.add_column('system_variables', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID，为空表示全局变量'))
    op.create_foreign_key('fk_system_variables_tenant_id', 'system_variables', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_system_variables_tenant', 'system_variables', ['tenant_id', 'name'])
    
    # 为 alerts 表添加 tenant_id
    op.add_column('alerts', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_alerts_tenant_id', 'alerts', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_alerts_tenant', 'alerts', ['tenant_id', 'task_id'])
    
    # 为 alert_configs 表添加 tenant_id
    op.add_column('alert_configs', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
    op.create_foreign_key('fk_alert_configs_tenant_id', 'alert_configs', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_alert_configs_tenant', 'alert_configs', ['tenant_id', 'task_id'])
    
    # 为 reports 表添加 tenant_id (如果存在)
    try:
        op.add_column('reports', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
        op.create_foreign_key('fk_reports_tenant_id', 'reports', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
        op.create_index('idx_reports_tenant', 'reports', ['tenant_id', 'report_type'])
    except:
        pass  # reports 表可能不存在
    
    # 为 report_subscriptions 表添加 tenant_id (如果存在)
    try:
        op.add_column('report_subscriptions', sa.Column('tenant_id', sa.String(36), nullable=True, comment='租户ID'))
        op.create_foreign_key('fk_report_subscriptions_tenant_id', 'report_subscriptions', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
        op.create_index('idx_report_subscriptions_tenant', 'report_subscriptions', ['tenant_id', 'report_id'])
    except:
        pass  # report_subscriptions 表可能不存在


def downgrade() -> None:
    # ### 删除索引和外键约束 ###
    
    # 删除 report_subscriptions 相关 (如果存在)
    try:
        op.drop_index('idx_report_subscriptions_tenant', 'report_subscriptions')
        op.drop_constraint('fk_report_subscriptions_tenant_id', 'report_subscriptions', type_='foreignkey')
        op.drop_column('report_subscriptions', 'tenant_id')
    except:
        pass
    
    # 删除 reports 相关 (如果存在)
    try:
        op.drop_index('idx_reports_tenant', 'reports')
        op.drop_constraint('fk_reports_tenant_id', 'reports', type_='foreignkey')
        op.drop_column('reports', 'tenant_id')
    except:
        pass
    
    # 删除 alert_configs 相关
    op.drop_index('idx_alert_configs_tenant', 'alert_configs')
    op.drop_constraint('fk_alert_configs_tenant_id', 'alert_configs', type_='foreignkey')
    op.drop_column('alert_configs', 'tenant_id')
    
    # 删除 alerts 相关
    op.drop_index('idx_alerts_tenant', 'alerts')
    op.drop_constraint('fk_alerts_tenant_id', 'alerts', type_='foreignkey')
    op.drop_column('alerts', 'tenant_id')
    
    # 删除 system_variables 相关
    op.drop_index('idx_system_variables_tenant', 'system_variables')
    op.drop_constraint('fk_system_variables_tenant_id', 'system_variables', type_='foreignkey')
    op.drop_column('system_variables', 'tenant_id')
    
    # 删除 nodes 相关
    op.drop_index('idx_nodes_tenant', 'nodes')
    op.drop_constraint('fk_nodes_tenant_id', 'nodes', type_='foreignkey')
    op.drop_column('nodes', 'tenant_id')
    
    # 删除 results 相关
    op.drop_index('idx_results_tenant', 'results')
    op.drop_constraint('fk_results_tenant_id', 'results', type_='foreignkey')
    op.drop_column('results', 'tenant_id')
    
    # 删除 tasks 相关
    op.drop_index('idx_tasks_tenant', 'tasks')
    op.drop_constraint('fk_tasks_tenant_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'tenant_id')
    
    # ### 删除用户-租户关联表 ###
    op.drop_index('idx_user_tenants_tenant_role', 'user_tenants')
    op.drop_table('user_tenants')
    
    # ### 删除租户表 ###
    op.drop_index('idx_tenants_subscription', 'tenants')
    op.drop_index('idx_tenants_status', 'tenants')
    op.drop_table('tenants')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS subscription_level_enum')
    op.execute('DROP TYPE IF EXISTS tenant_status_enum')
    op.execute('DROP TYPE IF EXISTS user_tenant_role_enum')