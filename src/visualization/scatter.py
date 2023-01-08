from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.offsetbox import AnnotationBbox, OffsetImage, TextArea

from src.visualization.helpers import unsnake
from src.visualization.logos import LogoMap


def get_team_scatter_ranker(df_play_info: pd.DataFrame) -> Callable:
    def ranker(method: str, formation: str):
        query = f"method == '{method}' and offenseFormation == '{formation}'"
        df = pd.DataFrame(df_play_info.query(query))
        df["team"] = df["possessionTeam"]
        df["time_in_pocket"] = df["frame_end"] - df["frame_start"]
        df["is_sack"] = (df["passResult"] == "S").astype(int)
        aggregations = {
            "plays": ("playId", len),
            "median_area": ("median_area", np.median),
            "median_time_in_pocket": ("time_in_pocket", np.median),
            "sack_rate": ("is_sack", np.mean),
        }
        df_gp = df.groupby(["team"]).agg(**aggregations).reset_index()
        df_gp["median_time_in_pocket"] = df_gp["median_time_in_pocket"] / 10.0
        df_out = df_gp.sort_values(
            by=["median_area"], ascending=False
        ).reset_index()
        return df_out

    return ranker


def plot_team_scatter(ax, logos, color, df, col_x, col_y):
    # Plot averages
    x_mean = df[col_x].mean()
    y_mean = df[col_y].mean()
    line_kwargs = dict(linestyle="--", color="lightgray", linewidth=1)
    ax.axvline(x_mean, **line_kwargs)
    ax.axhline(y_mean, **line_kwargs)
    # Plot data
    alpha = 1 if logos is None else 0
    ax.scatter(df[col_x], df[col_y], color=color, alpha=alpha)
    for tup in df[["team", col_x, col_y]].itertuples(index=False):
        team, x, y = tup
        if logos is not None:
            logo = AnnotationBbox(
                OffsetImage(logos[team], zoom=0.5), xy=(x, y), frameon=False
            )
            ax.add_artist(logo)
        text = AnnotationBbox(
            TextArea(team),
            xy=(x, y),
            xybox=(20, 0),
            xycoords="data",
            boxcoords="offset points",
            frameon=False,
        )
        ax.add_artist(text)
    # Configure plot
    ax.set_xlabel(unsnake(col_x))
    ax.set_ylabel(unsnake(col_y))


def get_team_scatter_plotter(
    df_play_info: pd.DataFrame, logos: LogoMap
) -> Callable:

    rank_team_scatter = get_team_scatter_ranker(df_play_info)

    def plot(method: str, formation: str, col_x: str, col_y: str):
        fig, ax = plt.subplots(1, 1)
        df = rank_team_scatter(method, formation)
        pal = sns.hls_palette(1)
        title = unsnake(f"Formation:_{formation},_Area:_{method}")
        ax.set_title(title)
        plot_team_scatter(ax, logos, pal[0], df, col_x, col_y)
        fig.set_size_inches(12, 12)
        plt.show()

    return plot
