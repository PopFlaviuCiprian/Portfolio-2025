"""Am eliminat level din skills

Revision ID: 6959a2ad1efe
Revises: 
Create Date: 2025-02-28 20:44:28.567330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6959a2ad1efe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.drop_column('level')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('skill', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level', sa.VARCHAR(length=200), nullable=True))

    # ### end Alembic commands ###
