"""empty message

Revision ID: 78cbdfb6e27d
Revises: None
Create Date: 2016-09-26 16:25:56.314834

"""

# revision identifiers, used by Alembic.
revision = '78cbdfb6e27d'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('comment')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###
