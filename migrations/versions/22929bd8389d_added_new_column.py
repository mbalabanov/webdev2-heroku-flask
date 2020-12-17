"""Added new column

Revision ID: 22929bd8389d
Revises: dcb04560b057
Create Date: 2020-12-17 19:45:14.055647

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22929bd8389d'
down_revision = 'dcb04560b057'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('profilepic', sa.BLOB(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'profilepic')
    # ### end Alembic commands ###
