"""Implement additional missing fields

Revision ID: 77606f05ceb3
Revises: 44a60691892c
Create Date: 2022-11-10 13:19:04.296953

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77606f05ceb3'
down_revision = '44a60691892c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('Artist', sa.Column('seeking_description', sa.String(), nullable=True))
    op.add_column('Venue', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.drop_column('Venue', 'website')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('website', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    op.drop_column('Venue', 'website_link')
    op.drop_column('Artist', 'seeking_description')
    op.drop_column('Artist', 'website_link')
    # ### end Alembic commands ###