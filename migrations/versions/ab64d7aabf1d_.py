"""empty message

Revision ID: ab64d7aabf1d
Revises: b7b730d0b816
Create Date: 2020-09-25 20:46:52.270726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab64d7aabf1d'
down_revision = 'b7b730d0b816'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('avatar', sa.String(length=200), nullable=True))
    op.add_column('user', sa.Column('tokens', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'tokens')
    op.drop_column('user', 'avatar')
    # ### end Alembic commands ###
