from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.offsetbox import AnnotationBbox, OffsetImage, TextArea

from src.visualization.helpers import unsnake
from src.visualization.logos import LogoMap

# https://teamcolorcodes.com/nfl-team-color-codes/
color_for_team = {
    "ARI": (151, 35, 63),
    "ATL": (167, 25, 48),
    "BAL": (26, 25, 95),
    "BUF": (0, 51, 141),
    "CAR": (0, 133, 202),
    "CHI": (11, 22, 42),
    "CIN": (251, 79, 20),
    "CLE": (49, 29, 0),
    "DAL": (0, 53, 148),
    "DEN": (251, 79, 20),
    "DET": (0, 118, 182),
    "GB": (24, 48, 40),
    "HOU": (3, 32, 47),
    "IND": (0, 44, 95),
    "JAX": (16, 24, 32),
    "KC": (227, 24, 55),
    "LAC": (0, 128, 198),
    "LA": (0, 53, 148),
    "MIA": (0, 142, 151),
    "MIN": (79, 38, 131),
    "NE": (0, 34, 68),
    "NO": (211, 188, 141),
    "NYG": (1, 35, 82),
    "NYJ": (18, 87, 64),
    "LV": (0, 0, 0),
    "PHI": (0, 76, 84),
    "PIT": (255, 182, 18),
    "SF": (170, 0, 0),
    "SEA": (0, 34, 68),
    "TB": (213, 10, 10),
    "TEN": (75, 146, 219),
    "WAS": (90, 20, 20),
    "LV": (165, 172, 175),
}


def get_team_scatter_ranker(df_play_info: pd.DataFrame) -> Callable:
    def ranker(method: str, formation: str):
        query = f"method == '{method}' and offenseFormation in ({formation})"
        df = pd.DataFrame(df_play_info.query(query))
        df["team"] = df["possessionTeam"]
        df["opponent"] = df["defensiveTeam"]
        df["time_in_pocket"] = df["frame_end"] - df["frame_start"]
        df["is_sack"] = (df["passResult"] == "S").astype(int)
        aggregations = {
            "plays": ("playId", len),
            "median_area": ("median_area", np.median),
            "median_time_in_pocket": ("time_in_pocket", np.median),
            "sack_rate": ("is_sack", np.mean),
        }

        df_opp = df.groupby(["opponent"]).agg(**aggregations).reset_index()
        df_gp = df.groupby(["team"]).agg(**aggregations).reset_index()

        df_out = df_gp.merge(
            df_opp,
            left_on=["team"],
            right_on="opponent",
            suffixes=["", "_opponent"],
            how="left",
        )

        df_out["median_time_in_pocket"] = df_out["median_time_in_pocket"] / 10.0
        df_out["median_time_in_pocket_opponent"] = (
            df_out["median_time_in_pocket_opponent"] / 10.0
        )
        df_out = df_out.sort_values(
            by=["median_area"], ascending=False
        ).reset_index(drop=True)
        df_out["rank"] = np.arange(1, len(df_out) + 1, 1)
        out_keys = ["rank", "team"]
        out_cols = [
            "plays",
            "median_area",
            "median_time_in_pocket",
            "sack_rate",
        ]
        out_cols_opp = [f"{col}_opponent" for col in out_cols]
        return df_out[out_keys + out_cols + out_cols_opp]

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
        names = [unsnake(f[1:-1]) for f in formation.split(", ")]
        formation_names = ", ".join(names)
        title = f"Area: {unsnake(method)}\nFormations: {formation_names}"
        ax.set_title(title)
        plot_team_scatter(ax, logos, pal[0], df, col_x, col_y)
        fig.set_size_inches(8, 8)

    return plot


def plot_rankings(df_in, team_logos, area_col, ascending):
    df_team_ranking = pd.DataFrame(df_in).sort_values(
        by=area_col, ascending=ascending
    )
    df_team_ranking["rank"] = np.arange(1, len(df_team_ranking) + 1, 1)
    fig, ax = plt.subplots(1, 1)
    pal = []
    for tup in df_team_ranking[["team", "rank", area_col]].itertuples(
        index=False
    ):
        team, x, y = tup
        if team_logos is not None:
            color = color_for_team[team]
            pal.append(color)
            team_logo = team_logos[team]
            logo = AnnotationBbox(
                OffsetImage(team_logo, zoom=0.35), xy=(x, y), frameon=False
            )
            ax.add_artist(logo)
        text = AnnotationBbox(
            TextArea(team),
            xy=(x, y),
            xybox=(0, 10),
            xycoords="data",
            boxcoords="offset points",
            fontsize=2,
            frameon=False,
        )
        ax.add_artist(text)
    pal = np.array(pal) / 255.0
    bar_width = 1
    ax.bar(
        x=df_team_ranking["rank"],
        height=df_team_ranking[area_col],
        width=bar_width,
        color=pal,
    )
    ax.axhline(
        df_team_ranking[area_col].max(), linestyle="--", color="lightgray"
    )
    ax.axhline(
        df_team_ranking[area_col].mean(), linestyle="--", color="lightgray"
    )
    ax.axhline(
        df_team_ranking[area_col].min(), linestyle="--", color="lightgray"
    )
    ax.set_ylim(0, 1.2 * df_team_ranking[area_col].max())
    ax.set_xticks(np.arange(1, len(df_team_ranking) + 1, 1))
    ax.set_xlabel("Team Rank")
    fig.set_size_inches(14, 4)
    return
