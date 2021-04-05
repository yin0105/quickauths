"""empty message

Revision ID: d807720dfe1c
Revises: 521474055254
Create Date: 2021-03-14 15:58:04.608502

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd807720dfe1c'
down_revision = '521474055254'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('php_eligibility', sa.Column('other_ins', sa.String(length=20), nullable=True))
    op.alter_column('php_pending_request', 'message',
               existing_type=sa.VARCHAR(length=30),
               nullable=True)
    op.alter_column('php_pending_request', 'refNumber',
               existing_type=sa.VARCHAR(length=30),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('php_pending_request', 'refNumber',
               existing_type=sa.VARCHAR(length=30),
               nullable=False)
    op.alter_column('php_pending_request', 'message',
               existing_type=sa.VARCHAR(length=30),
               nullable=False)
    op.drop_column('php_eligibility', 'other_ins')
    # ### end Alembic commands ###
