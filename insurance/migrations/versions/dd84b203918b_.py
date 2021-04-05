"""empty message

Revision ID: dd84b203918b
Revises: d66ff3dd4df3
Create Date: 2021-03-16 21:41:27.144448

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd84b203918b'
down_revision = 'd66ff3dd4df3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medi_cal_eligibility', schema=None) as batch_op:
        batch_op.add_column(sa.Column('firstName', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('lastName', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medi_cal_eligibility', schema=None) as batch_op:
        batch_op.drop_column('lastName')
        batch_op.drop_column('firstName')

    # ### end Alembic commands ###