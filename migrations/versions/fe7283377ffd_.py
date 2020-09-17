"""empty message

Revision ID: fe7283377ffd
Revises: 8b2a6f49aa84
Create Date: 2020-09-16 23:16:43.536606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe7283377ffd'
down_revision = '8b2a6f49aa84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_beernight',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('beernight_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['beernight_id'], ['beernight.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_beernight_admin',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('beernight_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['beernight_id'], ['beernight.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('user_beernight_memeber',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('beernight_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['beernight_id'], ['beernight.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.add_column('beernight', sa.Column('name', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('beernight', 'name')
    op.drop_table('user_beernight_memeber')
    op.drop_table('user_beernight_admin')
    op.drop_table('user_beernight')
    # ### end Alembic commands ###
