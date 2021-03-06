"""empty message

Revision ID: cda3e16db65c
Revises: 261a9686768d
Create Date: 2020-08-14 15:37:33.458468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cda3e16db65c'
down_revision = '261a9686768d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('num_sections', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'num_sections')
    # ### end Alembic commands ###
