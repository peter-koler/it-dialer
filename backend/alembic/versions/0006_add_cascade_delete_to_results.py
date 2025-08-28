"""add cascade delete to results table

Revision ID: 0006
Revises: 3c6bef228603
Create Date: 2025-08-16 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_add_cascade_delete_to_results'
down_revision: Union[str, None] = '0005_add_system_variables_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint('results_task_id_fkey', 'results', type_='foreignkey')
    
    # Create a new foreign key constraint with CASCADE delete
    op.create_foreign_key(
        'results_task_id_fkey', 
        'results', 
        'tasks', 
        ['task_id'], 
        ['id'], 
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop the CASCADE foreign key constraint
    op.drop_constraint('results_task_id_fkey', 'results', type_='foreignkey')
    
    # Create the original foreign key constraint without CASCADE
    op.create_foreign_key(
        'results_task_id_fkey', 
        'results', 
        'tasks', 
        ['task_id'], 
        ['id']
    )