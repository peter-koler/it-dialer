"""add audit logs table

Revision ID: 0012_add_audit_logs_table
Revises: 0011_add_max_users_and_unique_constraint
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0012_add_audit_logs_table'
down_revision = '0011_add_max_users_and_unique_constraint'
branch_labels = None
depends_on = None


def upgrade():
    # 创建审计日志表
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=50), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_target_user_id', 'audit_logs', ['target_user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # 创建外键约束
    op.create_foreign_key('fk_audit_logs_tenant_id', 'audit_logs', 'tenants', ['tenant_id'], ['id'])
    op.create_foreign_key('fk_audit_logs_user_id', 'audit_logs', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_audit_logs_target_user_id', 'audit_logs', 'users', ['target_user_id'], ['id'])


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_audit_logs_target_user_id', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_audit_logs_user_id', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_audit_logs_tenant_id', 'audit_logs', type_='foreignkey')
    
    # 删除索引
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_audit_logs_resource_id', 'audit_logs')
    op.drop_index('ix_audit_logs_resource_type', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_target_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_tenant_id', 'audit_logs')
    
    # 删除表
    op.drop_table('audit_logs')