import argparse
import configparser
import logging
import sys

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2.errors
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from wotstats.api import TIME_FIELDS, Realm, account_info
from wotstats.plotting import create_plot
from wotstats.sql import statistics
from wotstats.utils import flatten, timestamps_to_datetime

config = configparser.ConfigParser(allow_no_value=True)
config.read_dict(
    {
        "db": {"url": "postgresql://wotstats@localhost/wotstats"},
        "api": {"realm": "EU", "application-id": ""},
        "accounts": {},
        "plots": {},
        "logging": {"log-level": "INFO"},
    }
)

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="/etc/wotstats/wotstats.ini")


def main(args=None):
    args = parser.parse_args(args)
    config.read(args.config)

    try:
        logging.basicConfig(
            format="%(levelname)s:%(message)s", level=config["logging"]["log-level"]
        )
    except ValueError:
        logging.warning(
            f"Incorrect log-level specified: {config['logging']['log-level']}. "
            "Falling back to INFO."
        )
        logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    try:
        realm = Realm[config["api"]["realm"]]
    except KeyError:
        logging.critical(
            f"Configured realm \"{config['api']['realm']}\" is unknown. "
            f"Choose one of: {', '.join(Realm.__members__.keys())}"
        )
        sys.exit(1)

    if not len(config["accounts"]):
        logging.warning(
            "There are no configured accounts, nothing to do. "
            'Check the "accounts" section in the config file.'
        )

    try:
        account_data = account_info(
            realm,
            config["api"]["application-id"],
            list(config["accounts"].keys()),
        ).values()
    except ValueError as e:
        logging.critical(e)
        sys.exit(1)

    flat_account_data = [
        timestamps_to_datetime(flatten(data, strip=True), keys=TIME_FIELDS)
        for data in account_data
    ]

    rows = [
        {column.name: data[column.name] for column in statistics.columns}
        for data in flat_account_data
    ]

    try:
        with sa.create_engine(config["db"]["url"]).connect() as conn:
            changed = False
            for row in rows:
                logging.info(
                    f"Attempting insert {row['nickname']} @ {row['updated_at']}"
                )
                try:
                    conn.execute(
                        statistics.insert()
                        .values(row)
                        .compile(dialect=postgresql.dialect())
                    )
                    changed = True
                    logging.info("Insert successful")
                except IntegrityError as e:
                    if not isinstance(e.orig, psycopg2.errors.UniqueViolation):
                        raise e from e
                    logging.info(f"Skipping, record exists")

            if config["plots"] and changed:
                df = pd.read_sql(
                    "SELECT * from statistics ORDER BY updated_at",
                    conn,
                    index_col=["account_id", "updated_at"],
                )
                plt.style.use("Solarize_Light2")
                for path, interval_str in config["plots"].items():
                    if interval_str:
                        figure = create_plot(
                            df[
                                df.index.get_level_values(1)
                                > (
                                    pd.Timestamp.now(tz="UTC")
                                    - pd.Timedelta(interval_str)
                                )
                            ]
                        )
                    else:
                        figure = create_plot(df)
                    figure.savefig(path)

    except sa.exc.OperationalError as e:
        logging.critical(f"Invalid database URL: {config['db']['url']} ({e})")
        sys.exit(1)
    except sa.exc.NoSuchModuleError:
        logging.critical(f"Invalid protocol in database URL: {config['db']['url']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
