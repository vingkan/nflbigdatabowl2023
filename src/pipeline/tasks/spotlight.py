import numpy as np
import pandas as pd
from shapely import Point, Polygon


def get_spotlight_plays(df_play_metrics: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(df_play_metrics)
    # 1. Filter play_metrics to only the before_end time window
    df = df[df["window_type"] == "before_end"]
    # 2. Augment play_metrics with the percentage change of the area between the window start and end
    df["percentage_change"] = (df["area_start"] - df["area_end"]) / df[
        "area_start"
    ]
    # Temporary: Add back window start and end frames
    frames_per_second = 10
    df["window_start"] = (df["time_start"] * frames_per_second).astype(int)
    df["window_end"] = (df["time_end"] * frames_per_second).astype(int)
    # 3. Filter play_metrics to only plays with a high pocket area loss according to percentage change
    # Note: The caller can implement their own filtering on the returned DataFrame.
    return df


def get_frame_vertices(df_areas: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(df_areas)
    # 4. Augment pocket_areas with a column that contains the vertices from the pocket metadata, if any
    df["vertices"] = df["pocket"].apply(
        lambda p: p.get("metadata", {}).get("vertices")
    )
    # 5. Filter pocket_areas to only frames with vertices in the pocket metadata
    df = df[df["vertices"].notna()]
    df = df[["gameId", "playId", "frameId", "vertices"]]
    return df.reset_index()


def get_spotlight_windows(
    df_spotlight_plays: pd.DataFrame, df_frame_vertices: pd.DataFrame
) -> pd.DataFrame:
    # 6. Left join the filtered play_metrics to pocket_areas to get the vertices for the start and end frames
    play_keys = ["gameId", "playId"]
    df = (
        df_spotlight_plays.merge(
            df_frame_vertices,
            left_on=play_keys + ["window_start"],
            right_on=play_keys + ["frameId"],
            how="left",
        )
        .drop(columns=["frameId"])
        .rename(columns={"vertices": "vertices_start"})
        .merge(
            df_frame_vertices,
            left_on=play_keys + ["window_end"],
            right_on=play_keys + ["frameId"],
            how="left",
        )
        .drop(columns=["frameId"])
        .rename(columns={"vertices": "vertices_end"})
    )
    # 7. Filter the join result to only windows that have vertices for both their start and end frames
    df = df[df["vertices_start"].notna() & df["vertices_end"].notna()]
    # 8. Augment the join result with shapely polygons from the vertices
    df["polygon_start"] = df["vertices_start"].apply(lambda v: Polygon(v))
    df["polygon_end"] = df["vertices_end"].apply(lambda v: Polygon(v))
    # 9. Augment the join result the polygon difference between the start and end polygons
    def get_polygon_difference(polygon_start, polygon_end):
        return polygon_start.difference(polygon_end)

    vec_polygon_difference = np.vectorize(get_polygon_difference)
    df["polygon_difference"] = vec_polygon_difference(
        df["polygon_start"], df["polygon_end"]
    )
    # 10. This result provides spotlight_windows, the spotlight area for each selected play window
    return df


def get_spotlight_players(
    df_spotlight_windows: pd.DataFrame, df_tracking: pd.DataFrame
) -> pd.DataFrame:
    # 11. Filter tracking_display to blockers and rushers
    player_cols = [
        "gameId",
        "playId",
        "frameId",
        "nflId",
        "jerseyNumber",
        "pff_role",
        "x",
        "y",
    ]
    df_player_frames = pd.DataFrame(df_tracking[player_cols])
    pocket_roles = {"Pass Block", "Pass Rush"}
    df_player_frames = df_player_frames[
        df_player_frames["pff_role"].isin(pocket_roles)
    ]
    # 12. Left join spotlight_windows to tracking_display to get the filtered players for that frame
    df = df_spotlight_windows.merge(
        df_player_frames,
        left_on=["gameId", "playId", "window_start"],
        right_on=["gameId", "playId", "frameId"],
        how="left",
    )
    # 13. This result provides spotlight_players, the players that could be in the spotlight area
    # 14. Augment the join result with an indicator column for whether or not each player is in the spotlight area
    def is_in_spotlight(polygon, x, y):
        point = Point(x, y)
        return polygon.contains(point)

    vec_is_in_spotlight = np.vectorize(is_in_spotlight)
    df["in_spotlight"] = vec_is_in_spotlight(
        df["polygon_difference"], df["x"], df["y"]
    )
    # 15. Filter the join result to players who are in the spotlight area
    df = df[df["in_spotlight"]]
    return df


def get_spotlight_metrics(
    df_windows: pd.DataFrame, df_players: pd.DataFrame
) -> pd.DataFrame:
    def count_players_by_role(
        df_in: pd.DataFrame, role: str, name: str
    ) -> pd.DataFrame:
        df = pd.DataFrame(df_in)
        df = df[df["pff_role"] == role].reset_index()
        aggregations = {
            f"count_{name}": ("nflId", len),
            f"all_{name}": ("jerseyNumber", list),
        }
        return (
            df.groupby(["gameId", "playId"]).agg(**aggregations).reset_index()
        )

    df = pd.DataFrame(df_players)
    df["nflId"] = df["nflId"].astype(int).astype(str)
    # 16. Aggregate the players in the spotlight area to calculate how many blockers are in the spotlight area
    df_blockers = count_players_by_role(df, "Pass Block", "blockers")
    # 17. Aggregate the players in the spotlight area to calculate how many rushers are in the spotlight area
    df_rushers = count_players_by_role(df, "Pass Rush", "rushers")
    # 18. Left join spotlight_windows to the aggregated columns from spotlight_players
    # Note: This step is repeated so that we can left join to all windows and fill in missing values for
    # windows that do not have any players of the given role.
    play_keys = ["gameId", "playId"]
    df_left = df_windows[play_keys]
    df_metrics = (
        df_left.merge(df_blockers, on=play_keys, how="left")
        .merge(df_rushers, on=play_keys, how="left")
        .fillna(
            {
                "count_blockers": 0,
                "count_rushers": 0,
                "all_blockers": list,
                "all_rushers": list,
            }
        )
    )
    return df_metrics


def get_spotlight_search(
    df_windows: pd.DataFrame, df_metrics: pd.DataFrame, df_plays: pd.DataFrame
) -> pd.DataFrame:
    # 18. Left join spotlight_windows to the aggregated columns from spotlight_players
    # 19. Left join spotlight_windows to plays to pull in additional dimensions about the play
    play_keys = ["gameId", "playId"]
    df = df_windows.merge(df_metrics, on=play_keys, how="left").merge(
        df_plays, on=play_keys, how="left"
    )
    # 20. Query the augmented spotlight_windows to find spotlight moments of interest
    return df


def get_spotlight_data(
    df_tracking: pd.DataFrame,
    df_play_metrics: pd.DataFrame,
    df_areas: pd.DataFrame,
    df_plays: pd.DataFrame,
) -> pd.DataFrame:
    # The spotlight algorithm only works with area algorithms where the defender
    # can be in the pocket, and the adaptive pocket area algorithm is our best
    # algorithm in that category.
    default_area = "adaptive_pocket_area"
    query_area = f"method == '{default_area}'"
    df_play_metrics_default = df_play_metrics.query(query_area)
    df_areas_default = df_areas.query(query_area)
    # Run steps of algorithm.
    df_spotlight_plays = get_spotlight_plays(df_play_metrics_default)
    # Optional: We can pre-filter plays to reduce spatial computation below, or we can leave this for the end.
    # df_spotlight_plays = df_spotlight_plays[df_spotlight_plays["percentage_change"] >= 0.99]
    df_frame_vertices = get_frame_vertices(df_areas_default)
    df_spotlight_windows = get_spotlight_windows(
        df_spotlight_plays, df_frame_vertices
    )
    df_spotlight_players = get_spotlight_players(
        df_spotlight_windows, df_tracking
    )
    df_spotlight_metrics = get_spotlight_metrics(
        df_spotlight_windows, df_spotlight_players
    )
    df_spotlight_search = get_spotlight_search(
        df_spotlight_windows, df_spotlight_metrics, df_plays
    )
    return df_spotlight_search
