"""empty message

Revision ID: fee5e556d11c
Revises: 68aefb86b6c0
Create Date: 2020-10-16 01:39:00.469657

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fee5e556d11c'
down_revision = '68aefb86b6c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('game_score', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'game_score')
    # ### end Alembic commands ###
