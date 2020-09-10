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
    logging.basicConfig(level=logging.DEBUG)
    args = parser.parse_args(args)

    info = account_info(Realm[args.realm], args.application_id, args.account_ids)

    tuples = [
        (account_id, *(data[key] for key in fields))
        for account_id, data in info.items()
    ]

    with sa.create_engine("postgresql://wotstats@localhost/wotstats").connect() as conn:
        try:
            conn.execute(
                statistics.insert().values(tuples).compile(dialect=postgresql.dialect())
            )
        except IntegrityError as e:
            if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
                raise e from e
            pass


if __name__ == "__main__":
    main()
