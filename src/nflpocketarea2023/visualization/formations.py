from typing import Callable, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from nflpocketarea2023.visualization.helpers import unsnake


def plot_area_distributions(df_median_areas: pd.DataFrame):
    area_methods = list(df_median_areas["method"].unique())
    n_rows = 2
    n_cols = int(np.ceil(len(area_methods) / 2.0))
    fig, axes = plt.subplots(n_rows, n_cols)
    axes = [ax for row in axes for ax in row]
    pal = sns.hls_palette(len(area_methods))
    x_max = df_median_areas["median_area"].max()
    for i, method in enumerate(area_methods):
        ax = axes[i]
        color = pal[i]
        ser = df_median_areas["median_area"][df_median_areas.method == method]
        sns.histplot(ser, ax=ax, stat="percent", binwidth=10, color=color)
        ax.set_xlim(0, x_max)
        ax.set_title(unsnake(method))
        ax.set_xlabel("Median Area")
    fig.tight_layout()
    fig.set_size_inches(12, 8)
    plt.show()


def get_formation_distribution_plotter(
    df_play_info: pd.DataFrame, formations: List[str], x_max: float
) -> Callable:
    def plot(method: str, formation: str):
        fig, ax = plt.subplots(1, 1)
        color = sns.hls_palette(len(formations))[formations.index(formation)]
        df = df_play_info.query(f"method == '{method}'")
        ser = df["median_area"][df["offenseFormation"] == formation]
        ax.set_xlim(0, x_max)
        ax.set_title(unsnake(formation))
        ax.set_xlabel("Median Area")
        if len(ser) < 2:
            return
        sns.histplot(ser, ax=ax, stat="count", binwidth=10, color=color)
        plt.show()

    return plot


def get_all_formation_distributions_plotter(
    df_play_info: pd.DataFrame,
    formations: List[str],
) -> Callable:
    def plot(method: str):
        df = df_play_info.query(f"method == '{method}'")
        formations = df["offenseFormation"].unique()
        n_rows = 2
        n_cols = int(np.ceil(len(formations) / 2.0))
        fig, axes = plt.subplots(n_rows, n_cols)
        axes = [ax for row in axes for ax in row]
        pal = sns.hls_palette(len(formations))
        x_max = df["median_area"].max()
        y_max = df.groupby(["offenseFormation"])["gameId"].count().max()
        for i, formation in enumerate(formations):
            ax = axes[i]
            color = pal[i]
            ax.set_xlim(0, x_max)
            ax.set_ylim(0, y_max)
            ax.set_title(unsnake(formation))
            ax.set_xlabel("Median Area")
            ser = df["median_area"][df["offenseFormation"] == formation]
            if len(ser) < 2:
                continue
            sns.histplot(ser, ax=ax, stat="count", binwidth=10, color=color)
        fig.tight_layout()
        fig.set_size_inches(12, 8)
        plt.show()

    return plot
