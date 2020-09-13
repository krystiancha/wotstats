#!/usr/bin/env python3
import logging
import sys
import urllib.parse
from argparse import ArgumentParser
from collections.abc import MutableMapping
from os import SEEK_SET
from os.path import join

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import requests
from matplotlib import rcParams
from pandas.errors import EmptyDataError
from pandas.plotting import register_matplotlib_converters

API_ENDPOINT = "/wot/account/info/"
REQUEST_FIELDS = ("global_rating", "updated_at", "statistics.random", "nickname")
REQUEST_EXTRA = ("statistics.random",)
PRETTY_NAMES = {
    "global_rating": "Personal Rating",
    "avg_damage_assisted": "Average Assisted Damage",
    "avg_damage_blocked": "Average Blocked Damage",
    "avg_damage_dealt": "Average Damage",
    "avg_xp": "Average Experience",
    "wins_percents": "Victories",
    "avg_damage_assisted_radio": "Average Assisted Damage / Radio",
    "avg_stun_assisted_damage": "Average Assisted Damage / Stun",
    "avg_damage_assisted_track": "Average Assisted Damage / Track",
}


def flatten(iterable, parent_key="", sep="_"):
    items = []
    for key, value in iterable.items():
        new_key = (parent_key + sep + key if parent_key else key).replace(
            "statistics_random_", ""
        )
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def flattenadd(iterable, account_id):
    iterable = flatten(iterable)
    iterable.update({"account_id": account_id})
    return iterable


def get_data(file):
    try:
        df = pd.read_csv(file)
    except EmptyDataError:
        return pd.DataFrame(), True
    try:
        updated_at = df["updated_at"]
    except KeyError as e:
        raise TypeError("Invalid data file contents") from e
    df["updated_at"] = pd.to_datetime(updated_at)
    df.set_index(["updated_at", "account_id"], inplace=True)

    return df, False


def fast_cleanup(df):
    # Battle avgs
    for name in [
        "spotted",
        "capture_points",
        "explosion_hits",
        "piercings",
        "dropped_capture_points",
        "damage_dealt",
        "damage_received",
        "frags",
        "direct_hits_received",
        "hits",
        "piercings_received",
        "no_damage_direct_hits_received",
        "shots",
        "explosion_hits_received",
        "xp",
    ]:
        df[f"avg_{name}"] = df[name] / df["battles"]
        df.drop(name, axis="columns", inplace=True)

    # Battle percents
    for name in [
        "draws",
        "losses",
        "survived_battles",
        "wins",
    ]:
        df[f"{name}_percents"] = 100 * df[name] / df["battles"]
        df.drop(name, axis="columns", inplace=True)

    # Stun battles avgs
    for name in [
        "stun_assisted_damage",
        "stun_number",
    ]:
        df[f"avg_{name}"] = df[name] / df["battles_on_stunning_vehicles"]
        df.drop(name, axis="columns", inplace=True)

    # Remove total xp
    df.drop("battle_avg_xp", axis="columns", inplace=True)


def split_players(df, only_recent=False):
    dfs = {
        nickname: df[df["nickname"] == nickname].drop("nickname", axis="columns")
        for nickname in df["nickname"].unique()
    }

    for key in dfs:
        dfs[key].index = pd.DatetimeIndex(dfs[key].index.get_level_values(0))

    if only_recent:
        return {nickname: f.iloc[-1] for nickname, f in dfs.items()}

    return dfs


def ax_k(ax):
    formatter = ticker.FuncFormatter(lambda x, pos: f"{round(x / 1000, 2)}k")
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.set_minor_formatter(formatter)


def ax_percent(ax):
    formatter = ticker.StrMethodFormatter("{x:.2f}%")

    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.25))
    ax.yaxis.set_minor_formatter(formatter)


def fetch_stats(api_root, application_id, account_ids):
    response = requests.get(
        url=urllib.parse.urljoin(api_root, API_ENDPOINT),
        params={
            "application_id": application_id,
            "account_id": ",".join(account_ids),
            "fields": ",".join(REQUEST_FIELDS),
            "extra": ",".join(REQUEST_EXTRA),
        },
    )

    df = pd.DataFrame(
        [flattenadd(value, key) for key, value in response.json()["data"].items()]
    )
    df.dropna("columns", inplace=True)
    df["updated_at"] = pd.to_datetime(df["updated_at"], unit="s")
    df["account_id"] = df["account_id"].astype(int)
    df.set_index(["updated_at", "account_id"], inplace=True)
    df.sort_index(inplace=True)

    return df


def plot(dfs, filename, updated_at):
    fig: plt.Figure
    ax: plt.Axes
    fig = plt.figure(figsize=(2.75 * 6.4, 2.75 * 4.8))

    axes = {
        "global_rating": (fig.add_subplot(3, 3, 1), ax_k),
        "avg_damage_assisted": (fig.add_subplot(3, 3, 2), None),
        "avg_damage_blocked": (fig.add_subplot(3, 3, 3), None),
        "avg_damage_dealt": (fig.add_subplot(3, 3, 4), None),
        "avg_xp": (fig.add_subplot(3, 3, 5), None),
        "wins_percents": (fig.add_subplot(3, 3, 6), ax_percent),
        "avg_damage_assisted_radio": (fig.add_subplot(3, 3, 7), None),
        "avg_stun_assisted_damage": (fig.add_subplot(3, 3, 8), None),
        "avg_damage_assisted_track": (fig.add_subplot(3, 3, 9), None),
    }

    for name, (ax, ax_function) in axes.items():
        ax.set_title(PRETTY_NAMES[name], color=rcParams["axes.labelcolor"])
        for nickname, stats_df in dfs.items():
            if (stats_df[name] != 0).any(axis="rows"):
                ax.plot(
                    mdates.date2num(pd.to_datetime(stats_df[name].index)),
                    stats_df[name].values,
                )
        for nickname, stats_df in dfs.items():
            if (stats_df[name] != 0).any(axis="rows"):
                x_span = ax.get_xlim()[1] - ax.get_xlim()[0]
                no_nan = stats_df[name].dropna()
                ax.annotate(
                    f"{nickname}: {stats_df[name][-1]:.2f}",
                    xy=(ax.get_xlim()[1] - 0.01 * x_span, stats_df[name][-1]),
                    xycoords="data",
                    xytext=(0, 5),
                    textcoords="offset points",
                    horizontalalignment="right",
                    color=rcParams["axes.labelcolor"],
                )
                try:
                    delta = no_nan[-1] - no_nan[-2]
                    ax.annotate(
                        f"{delta:+.2f}",
                        xy=(no_nan.index[-1], no_nan[-1]),
                        xycoords="data",
                        xytext=(5, -2),
                        textcoords="offset points",
                        horizontalalignment="left",
                        verticalalignment="top",
                        color="#859900" if delta > 0 else "#dc322f",
                    )
                except IndexError:
                    pass
                val_max = stats_df[name].max()
                ax.axhline(val_max, linestyle="--", color="#93a1a1", linewidth=1)
                ax.annotate(
                    f"max. {stats_df[name].max():.2f}",
                    xy=(ax.get_xlim()[0] + 0.01 * x_span, val_max),
                    xycoords="data",
                    xytext=(0, 5),
                    textcoords="offset points",
                    horizontalalignment="left",
                    color=rcParams["axes.labelcolor"],
                )
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter("%d %b"))
        if ax_function:
            ax_function(ax)
        ax.grid(which="minor", axis="y")
        ax.grid(which="major", axis="y", linewidth=2)

    fig.tight_layout(pad=1.5)
    fig.text(
        0.001,
        0.001,
        f"Updated: {updated_at} UTC",
        color=rcParams["axes.labelcolor"],
    )

    fig.savefig(
        filename,
        facecolor=rcParams["figure.facecolor"],
        edgecolor=rcParams["figure.edgecolor"],
    )


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument("datafile", help="file containing stats history")
    parser.add_argument("plotdir", help="directory where the plots will be created")
    parser.add_argument(
        "--application-id", required=True, help="get one from developers.wargaming.net"
    )
    parser.add_argument(
        "--account", nargs="+", required=True, help="ids of accounts to track"
    )
    parser.add_argument(
        "--api-root",
        default="https://api.worldoftanks.eu",
        help="API root for your realm (defaults to EU API)",
    )
    parser.add_argument("--clean", action="store_true", help="clean the datafile")
    parser.add_argument(
        "--nofetch", action="store_true", help="don't fetch current stats"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="be more verbose")
    args = parser.parse_args(args)

    logging.basicConfig(level=(logging.INFO if args.verbose else logging.WARNING))

    datafile = open(args.datafile, "a+")
    datafile.seek(0, SEEK_SET)

    try:
        df, created = get_data(datafile)
    except TypeError as e:
        logging.error(str(e))
        sys.exit(1)

    if not args.nofetch:
        df2 = fetch_stats(args.api_root, args.application_id, args.account)
        df = df.append(df2, sort=False)
    df = df.loc[~(df.index.duplicated(keep="first"))]

    if df.empty:
        logging.error("No data available")
        sys.exit(1)

    if args.clean:
        datafile.close()
        datafile = open(args.datafile, "w")
        df.to_csv(datafile, header=True, line_terminator="\n")
    elif not args.nofetch:
        df2.to_csv(datafile, header=created, line_terminator="\n")
    datafile.close()

    fast_cleanup(df)

    register_matplotlib_converters()
    plt.style.use("Solarize_Light2")

    plot(
        split_players(df),
        join(args.plotdir, "all.svg"),
        df.index.get_level_values(0).to_series().idxmax(),
    )

    plot(
        split_players(
            df[
                (pd.Timestamp.now() - df.index.get_level_values(0))
                <= pd.Timedelta(30, "d")
            ]
        ),
        join(args.plotdir, "30d.svg"),
        df.index.get_level_values(0).to_series().idxmax(),
    )


if __name__ == "__main__":
    main()
