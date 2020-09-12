import argparse
import logging

import psycopg2.errors
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from wotstats.api import Realm, account_info
from wotstats.sql import fields, statistics

parser = argparse.ArgumentParser()
parser.add_argument("--realm", choices=Realm.__members__, required=True)
parser.add_argument("--application-id", required=True)
parser.add_argument("--account-id", action="append", required=True, dest="account_ids")


def main(args=None):
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args(args)

    info = account_info(Realm[args.realm], args.application_id, args.account_ids)

    tuples = [
        (account_id, *(data[key] for key in fields))
        for account_id, data in info.items()
    ]

    with sa.create_engine("postgresql://wotstats@localhost/wotstats").connect() as conn:
        for row in tuples:
            try:
                conn.execute(
                    statistics.insert().values(row).compile(dialect=postgresql.dialect())
                )
                logging.info("Updated table")
            except IntegrityError as e:
                if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise e from e
                logging.info(f"No new data: {e}")


if __name__ == "__main__":
    main()
