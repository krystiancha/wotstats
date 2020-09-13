import argparse
import csv
import logging
from typing import Sequence

import psycopg2
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError, OperationalError

from wotstats.sql import statistics

parser = argparse.ArgumentParser()
parser.add_argument("infile", type=argparse.FileType())
parser.add_argument("--db-url", default="postgresql://wotstats@localhost/wotstats")
parser.add_argument("--log-level", default="INFO")

if __name__ == "__main__":
    args = parser.parse_args()

    logging.basicConfig(
        format="%(levelname)s:%(message)s",
        level=args.log_level,
    )

    header: Sequence[str] = []
    records_added = 0
    try:
        with sa.create_engine(args.db_url).connect() as conn:
            for row in csv.reader(args.infile):
                if not header:
                    header = row
                    logging.info(f"Header: {header}")
                    continue
                row_dict = {key: value for key, value in zip(header, row)}

                record = tuple(
                    row_dict.get(key)
                    for key in map(lambda x: x.name, statistics.columns)
                )

                try:
                    conn.execute(statistics.insert().values(record))
                    records_added += 1
                    logging.info(
                        f"Added record: {row_dict['account_id']} @ {row_dict['updated_at']}"
                    )
                except IntegrityError as e:
                    if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
                        raise e from e
                    logging.info(
                        f"Skipped record: {row_dict['account_id']} @ {row_dict['updated_at']}"
                    )
    except OperationalError as e:
        logging.error(f"Could not connect to database server: {e}")

    logging.info(f"Added {records_added} records")
