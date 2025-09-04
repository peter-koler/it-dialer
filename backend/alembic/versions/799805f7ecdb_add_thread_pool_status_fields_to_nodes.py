"""add thread pool status fields to nodes

Revision ID: 799805f7ecdb
Revises: cda87509a03b
Create Date: 2025-09-04 15:45:15.708848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799805f7ecdb'
down_revision: Union[str, None] = 'cda87509a03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加线程池状态字段
    op.add_column('nodes', sa.Column('max_workers', sa.Integer(), nullable=True, comment='最大工作线程数'))
    op.add_column('nodes', sa.Column('active_threads', sa.Integer(), nullable=True, comment='活跃线程数'))
    op.add_column('nodes', sa.Column('completed_tasks', sa.Integer(), nullable=True, comment='已完成任务数'))
    op.add_column('nodes', sa.Column('pending_tasks', sa.Integer(), nullable=True, comment='等待任务数'))
    
    # 添加任务状态统计字段
    op.add_column('nodes', sa.Column('total_tasks', sa.Integer(), nullable=True, comment='总任务数'))
    op.add_column('nodes', sa.Column('running_tasks', sa.Integer(), nullable=True, comment='运行中任务数'))
    op.add_column('nodes', sa.Column('failed_tasks', sa.Integer(), nullable=True, comment='失败任务数'))


def downgrade() -> None:
    # 移除任务状态统计字段
    op.drop_column('nodes', 'failed_tasks')
    op.drop_column('nodes', 'running_tasks')
    op.drop_column('nodes', 'total_tasks')
    
    # 移除线程池状态字段
    op.drop_column('nodes', 'pending_tasks')
    op.drop_column('nodes', 'completed_tasks')
    op.drop_column('nodes', 'active_threads')
    op.drop_column('nodes', 'max_workers')
