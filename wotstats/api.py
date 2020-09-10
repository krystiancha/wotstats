import json
from collections.abc import MutableMapping
from datetime import datetime
from enum import Enum
from typing import Sequence
from urllib.parse import urljoin
from urllib.request import urlopen

FIELDS = [
    "last_battle_time",
    "updated_at",
    "global_rating",
    "clan_id",
    "statistics.trees_cut",
    "statistics.random.spotted",
    "statistics.random.battles_on_stunning_vehicles",
    "statistics.random.avg_damage_blocked",
    "statistics.random.capture_points",
    "statistics.random.explosion_hits",
    "statistics.random.piercings",
    "statistics.random.xp",
    "statistics.random.avg_damage_assisted",
    "statistics.random.dropped_capture_points",
    "statistics.random.damage_dealt",
    "statistics.random.hits_percents",
    "statistics.random.draws",
    "statistics.random.tanking_factor",
    "statistics.random.battles",
    "statistics.random.damage_received",
    "statistics.random.survived_battles",
    "statistics.random.frags",
    "statistics.random.stun_number",
    "statistics.random.avg_damage_assisted_radio",
    "statistics.random.direct_hits_received",
    "statistics.random.stun_assisted_damage",
    "statistics.random.hits",
    "statistics.random.battle_avg_xp",
    "statistics.random.wins",
    "statistics.random.losses",
    "statistics.random.piercings_received",
    "statistics.random.no_damage_direct_hits_received",
    "statistics.random.shots",
    "statistics.random.explosion_hits_received",
    "statistics.random.avg_damage_assisted_track",
    "nickname",
    "logout_at",
]

EXTRA = ["statistics.random"]

TIME_FIELDS = ["last_battle_time", "updated_at", "logout_at"]


class Realm(Enum):
    RU = "https://api.worldoftanks.ru/wot/"
    EU = "https://api.worldoftanks.eu/wot/"
    NA = "https://api.worldoftanks.com/wot/"
    ASIA = "https://api.worldoftanks.asia/wot/"


def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def parse(body):
    raw = json.load(body)

    for account, data in raw["data"].items():
        for field in TIME_FIELDS:
            data[field] = datetime.utcfromtimestamp(data[field])

    return {
        account: {
            key.replace("statistics.", "").replace("random.", ""): value
            for key, value in flatten(data, sep=".").items()
        }
        for account, data in raw["data"].items()
    }


def account_info(realm: Realm, application_id: str, account_ids: Sequence[str]):
    data = "&".join(
        [
            f"{key}={value}"
            for key, value in {
                "application_id": application_id,
                "account_id": ",".join(account_ids),
                "fields": ",".join(FIELDS),
                "extra": ",".join(EXTRA),
            }.items()
        ]
    )
    with urlopen(
        url=urljoin(realm.value, "account/info/"),
        data=data.encode(),
    ) as f:
        return parse(f)
