import argparse
import logging

import psycopg2.errors
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from wotstats.api import Realm, account_info
from wotstats.sql import statistics

parser = argparse.ArgumentParser()
parser.add_argument("--realm", choices=Realm.__members__, required=True)
parser.add_argument("--application-id", required=True)
parser.add_argument("--account-id", action="append", required=True, dest="account_ids")


def main(args=None):
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args(args)

    info = account_info(Realm[args.realm], args.application_id, args.account_ids)

    tuples = [tuple(data[x.name] for x in statistics.columns) for data in info.values()]

    with sa.create_engine("postgresql://wotstats@localhost/wotstats").connect() as conn:
        for row in tuples:
            try:
                conn.execute(
                    statistics.insert()
                    .values(row)
                    .compile(dialect=postgresql.dialect())
                )
                logging.info("Record added")
            except IntegrityError as e:
                if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise e from e
                logging.info(f"Record exists, skipping")


if __name__ == "__main__":
    main()
