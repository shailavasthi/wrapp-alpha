"""empty message

Revision ID: 2e1eb1c9c4db
Revises: fa4671c2d285
Create Date: 2020-08-18 10:30:58.508247

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e1eb1c9c4db'
down_revision = 'fa4671c2d285'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('drafts', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'drafts')
    # ### end Alembic commands ###
