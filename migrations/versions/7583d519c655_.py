"""empty message

Revision ID: 7583d519c655
Revises: 0d68d5bb71bf
Create Date: 2020-09-16 01:38:51.035443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7583d519c655'
down_revision = '0d68d5bb71bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('beer', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('beer', 'created_at')
    # ### end Alembic commands ###
