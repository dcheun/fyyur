"""Add order by for show relationship

Revision ID: 527bbc205da2
Revises: 77606f05ceb3
Create Date: 2022-11-13 06:07:37.515383

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '527bbc205da2'
down_revision = '77606f05ceb3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Show', 'start_time',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Show', 'start_time',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###
