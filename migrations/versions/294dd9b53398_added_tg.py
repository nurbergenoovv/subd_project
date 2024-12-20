"""added tg

Revision ID: 294dd9b53398
Revises: 
Create Date: 2024-10-03 03:29:12.970052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '294dd9b53398'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('counter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('current_counter', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_counter_id'), 'counter', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_counter_id'), table_name='counter')
    op.drop_table('counter')
    # ### end Alembic commands ###
