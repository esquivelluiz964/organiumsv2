"""add responsavel_id and setor_id to Event

Revision ID: 95299f0cf189
Revises: ec7f92e30b26
Create Date: 2025-09-25 11:18:50.730135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95299f0cf189'
down_revision = 'ec7f92e30b26'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('responsavel_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('setor_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cor', sa.String(length=7), nullable=True))
        batch_op.add_column(sa.Column('tipo', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_event_setor', 'sector', ['setor_id'], ['id'])
        batch_op.create_foreign_key('fk_event_responsavel', 'collaborator', ['responsavel_id'], ['id'])



def downgrade():
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.drop_constraint('fk_event_setor', type_='foreignkey')
        batch_op.drop_constraint('fk_event_responsavel', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('tipo')
        batch_op.drop_column('cor')
        batch_op.drop_column('setor_id')
        batch_op.drop_column('responsavel_id')

