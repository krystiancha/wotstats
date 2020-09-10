"""create statistics table

Revision ID: 9d1bc39b8198
Revises: 
Create Date: 2020-09-10 18:53:24.112358

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d1bc39b8198'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "statistics",
        sa.Column("account_id", sa.Integer, primary_key=True),
        sa.Column("battles_on_stunning_vehicles", sa.Integer),
        sa.Column("spotted", sa.Integer),
        sa.Column("avg_damage_blocked", sa.Float),
        sa.Column("direct_hits_received", sa.Integer),
        sa.Column("explosion_hits", sa.Integer),
        sa.Column("piercings", sa.Integer),
        sa.Column("xp", sa.Integer),
        sa.Column("avg_damage_assisted", sa.Float),
        sa.Column("dropped_capture_points", sa.Integer),
        sa.Column("piercings_received", sa.Integer),
        sa.Column("hits_percents", sa.Integer),
        sa.Column("draws", sa.Integer),
        sa.Column("battles", sa.Integer),
        sa.Column("damage_received", sa.Integer),
        sa.Column("survived_battles", sa.Integer),
        sa.Column("avg_damage_assisted_track", sa.Float),
        sa.Column("frags", sa.Integer),
        sa.Column("stun_number", sa.Integer),
        sa.Column("avg_damage_assisted_radio", sa.Float),
        sa.Column("capture_points", sa.Integer),
        sa.Column("stun_assisted_damage", sa.Integer),
        sa.Column("hits", sa.Integer),
        sa.Column("battle_avg_xp", sa.Integer),
        sa.Column("wins", sa.Integer),
        sa.Column("losses", sa.Integer),
        sa.Column("damage_dealt", sa.Integer),
        sa.Column("no_damage_direct_hits_received", sa.Integer),
        sa.Column("shots", sa.Integer),
        sa.Column("explosion_hits_received", sa.Integer),
        sa.Column("tanking_factor", sa.Numeric(2)),
        sa.Column("trees_cut", sa.Integer),
        sa.Column("last_battle_time", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("global_rating", sa.Integer),
        sa.Column("clan_id", sa.Integer),
        sa.Column("nickname", sa.String),
        sa.Column("logout_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("statistics")
