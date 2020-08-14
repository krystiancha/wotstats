import argparse
import csv
import json
import logging
from datetime import datetime
from urllib.request import urlopen

from wotstats.const import EXTRA_FIELDS, FIELD_ORDER, REALM_TO_API_ROOT, REGULAR_FIELDS
from wotstats.utils import flatten


class RealmAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, REALM_TO_API_ROOT[values])


def scrape(api_root, application_id, account_ids):
    with urlopen(
        f"{api_root}account/info/"
        f"?application_id={application_id}"
        f"&account_id={','.join(account_ids)}"
        f"&extra={','.join(EXTRA_FIELDS)}"
        f"&fields={','.join(REGULAR_FIELDS + EXTRA_FIELDS)}",
    ) as f:
        response_body = json.load(f)
        try:
            data = response_body.pop("data")
        finally:
            logging.info(f"Fetched stats, {response_body}")

        return [flatten(x) for x in data.values()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and store latest WoT player stats."
    )
    parser.add_argument(
        "--realm",
        action=RealmAction,
        choices=REALM_TO_API_ROOT.keys(),
        required=True,
        help="the WoT server name",
        dest="api_root",
    )
    parser.add_argument(
        "--app-id",
        required=True,
        help="application id obtained from developers.wargaming.net",
    )
    parser.add_argument(
        "--account-id",
        required=True,
        action="append",
        help="id of an account to fetch stats for, can be specified multiple times",
        dest="account_ids",
    )
    parser.add_argument(
        "--output", type=argparse.FileType("r+", encoding="utf-8"), required=True
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    args = parser.parse_args()

    logging.basicConfig(format="%(levelname)s:%(message)s", level=args.log_level)

    reader = csv.reader(args.output)
    writer = csv.writer(args.output)

    latest_rows = [
        [str(entry[field]) for field in FIELD_ORDER]
        for entry in scrape(args.api_root, args.app_id, args.account_ids)
    ]

    # determine which rows already exist in the file
    is_new = [True] * len(latest_rows)
    for row in reader:
        try:
            idx = latest_rows.index(row)
            is_new[idx] = False
        except ValueError:
            pass

    for new, row in zip(is_new, latest_rows):
        if new:
            player = row[FIELD_ORDER.index("account_id")]
            updated = datetime.fromtimestamp(int(row[FIELD_ORDER.index("updated_at")]))
            logging.info(f"Adding player {player} data updated at {updated}.")

    writer.writerows([row for new, row in zip(is_new, latest_rows) if new])
