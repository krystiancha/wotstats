from dataclasses import dataclass
from math import ceil
from typing import Optional

import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
import pandas as pd
import sqlalchemy as sa


@dataclass
class Plot:
    name: str
    column: str
    avg_column: Optional[str] = None
    percent: bool = False


PLOTS = [
    Plot("Personal Rating", "global_rating"),
    Plot("Average Assisted Damage", "avg_damage_assisted"),
    Plot("Average Blocked Damage", "avg_damage_blocked"),
    Plot("Average Damage", "damage_dealt", "battles"),
    Plot("Average Experience", "xp", "battles"),
    Plot("Victories", "wins", "battles", percent=True),
    Plot("Average Assisted Damage / Radio", "avg_damage_assisted_radio"),
    Plot(
        "Average Assisted Damage / Stun",
        "stun_assisted_damage",
        "battles_on_stunning_vehicles",
    ),
    Plot("Average Assisted Damage / Track", "avg_damage_assisted_track"),
    Plot("Trees cut", "trees_cut", "battles"),
]

NCOLS = 3


def get_series(df, plot, account_id):
    account_series = df[df.index.get_level_values(0) == account_id]
    series = account_series[plot.column]
    if plot.avg_column:
        series /= account_series[plot.avg_column]
        if plot.percent:
            series *= 100

    return series


def annotate_updated(fig, time):
    fig.text(
        0.001,
        0.001,
        f"Updated: {time} UTC",
        color=matplotlib.rcParams["axes.labelcolor"],
    )


def annotate_current(ax, series, nickname):
    ax.annotate(
        f"{nickname}: {series.iloc[-1]:.2f}",
        xy=(ax.get_xlim()[1], series.iloc[-1]),
        xycoords="data",
        xytext=(0, 5),
        textcoords="offset points",
        horizontalalignment="right",
        color=matplotlib.rcParams["axes.labelcolor"],
    )


def annotate_delta(ax, series):
    delta = series.iloc[-1] - series.iloc[-2]
    ax.annotate(
        f"{delta:+.2f}",
        xy=(ax.get_xlim()[1], series.iloc[-1]),
        xycoords="data",
        xytext=(-10, 0),
        textcoords="offset points",
        horizontalalignment="left",
        verticalalignment="center",
        color="#859900" if delta > 0 else "#dc322f",
    )


def annotate_max(ax, series):
    val_max = series.max()
    ax.axhline(val_max, linestyle="--", color="#93a1a1", linewidth=1)
    ax.annotate(
        f"max. {val_max:.2f}",
        xy=(ax.get_xlim()[0], val_max),
        xycoords="data",
        xytext=(0, 5),
        textcoords="offset points",
        horizontalalignment="left",
        color=matplotlib.rcParams["axes.labelcolor"],
    )


def create_plot(df):
    nrows = ceil(len(PLOTS) / NCOLS)
    fig, axes = plt.subplots(nrows, NCOLS, squeeze=False, figsize=(18, 18))
    for idx, plot in enumerate(PLOTS):
        ax = axes[idx // NCOLS, idx % NCOLS]
        ax.set_title(plot.name, color=matplotlib.rcParams["axes.labelcolor"])
        for account_id in df.index.get_level_values(0).unique():
            nickname = df[df.index.get_level_values(0) == account_id]["nickname"].iloc[
                -1
            ]
            series = get_series(df, plot, account_id)
            ax.step(series.index.get_level_values(1), series.values)
            annotate_current(ax, series, nickname)
            annotate_delta(ax, series)
            annotate_max(ax, series)

        for label in ax.get_xticklabels():
            label.set_ha("right")
            label.set_rotation(30)

    annotate_updated(fig, df.index.get_level_values(1).max())
    plt.tight_layout()

    return fig


if __name__ == "__main__":
    with sa.create_engine("postgresql://wotstats@localhost/wotstats").connect() as conn:
        df = pd.read_sql(
            "SELECT * from statistics ORDER BY updated_at",
            conn,
            index_col=["account_id", "updated_at"],
        )

    plt.style.use("Solarize_Light2")

    figure = create_plot(df)
    figure.savefig("fig.svg")
