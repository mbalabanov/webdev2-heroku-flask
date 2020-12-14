"""add hobby to user table

Revision ID: dcb04560b057
Revises: 4d8df9747099
Create Date: 2020-12-14 20:25:59.416344

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dcb04560b057'
down_revision = '4d8df9747099'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('hobby', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'hobby')
    # ### end Alembic commands ###