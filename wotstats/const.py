REALM_TO_API_ROOT = {
    "ru": "https://api.worldoftanks.ru/wot/",
    "eu": "https://api.worldoftanks.eu/wot/",
    "na": "https://api.worldoftanks.com/wot/",
    "asia": "https://api.worldoftanks.asia/wot/",
}

REGULAR_FIELDS = [
    "account_id",
    "global_rating",
    "last_battle_time",
    "logout_at",
    "updated_at",
    "statistics.trees_cut",
]

EXTRA_FIELDS = ["statistics.random"]

FIELD_ORDER = [
    *REGULAR_FIELDS,
    "statistics.random.avg_damage_assisted",
    "statistics.random.avg_damage_assisted_radio",
    "statistics.random.avg_damage_assisted_track",
    "statistics.random.avg_damage_blocked",
    "statistics.random.battle_avg_xp",
    "statistics.random.battles",
    "statistics.random.battles_on_stunning_vehicles",
    "statistics.random.capture_points",
    "statistics.random.damage_dealt",
    "statistics.random.damage_received",
    "statistics.random.direct_hits_received",
    "statistics.random.draws",
    "statistics.random.dropped_capture_points",
    "statistics.random.explosion_hits",
    "statistics.random.explosion_hits_received",
    "statistics.random.frags",
    "statistics.random.hits",
    "statistics.random.hits_percents",
    "statistics.random.losses",
    "statistics.random.no_damage_direct_hits_received",
    "statistics.random.piercings",
    "statistics.random.piercings_received",
    "statistics.random.shots",
    "statistics.random.spotted",
    "statistics.random.stun_assisted_damage",
    "statistics.random.stun_number",
    "statistics.random.survived_battles",
    "statistics.random.tanking_factor",
    "statistics.random.wins",
    "statistics.random.xp",
]
