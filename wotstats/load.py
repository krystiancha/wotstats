import argparse
import csv
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from wotstats.sql import fields, statistics

parser = argparse.ArgumentParser()
parser.add_argument("infile", type=argparse.FileType())

if __name__ == "__main__":
    args = parser.parse_args()

    header: Sequence[str] = []
    tuples = []
    for row in csv.reader(args.infile):
        if not header:
            header = row
            continue
        row_dict = {key: value for key, value in zip(header, row)}
        tuples.append(tuple(row_dict.get(key) for key in ["account_id"] + fields))
        print(tuples[-1])

    with sa.create_engine("postgresql://wotstats@localhost/wotstats").connect() as conn:
        conn.execute(
            statistics.insert().values(tuples).compile(dialect=postgresql.dialect())
        )
