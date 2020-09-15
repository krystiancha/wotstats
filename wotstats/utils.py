from collections.abc import MutableMapping
from datetime import datetime


def timestamps_to_datetime(d, keys=None):
    d = d.copy()
    for key in keys:
        try:
            d[key] = datetime.utcfromtimestamp(d[key])
        except KeyError:
            pass

    return d


def flatten(d, parent_key="", sep=".", strip=False):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key and not strip else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep, strip=strip).items())
        else:
            items.append((new_key, v))
    return dict(items)
