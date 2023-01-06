import numpy as np
import pandas as pd


def get_average_pocket_area_loss_per_second(
    area_start, area_end, time_start, time_end
):
    time_delta = time_end - time_start
    if time_delta == 0:
        return 0

    area_delta = area_end - area_start
    return area_delta / time_delta


def calculate_average_pocket_area_loss_per_second(
    df_play_pocket_metrics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Parameters:
    df_play_pocket_metrics: DataFrame for every play, pocket area method,
        and window type, with metrics related to pocket area.
      Contains columns:
        - gameId (PK)
        - playId (PK)
        - method (PK)
        - window_type (PK)
        - area_start
        - area_end
        - time_start
        - time_end

    Returns:
        DataFrame with pocket are loss per second for each primary key.
    Contains columns:
        - gameId (PK)
        - playId (PK)
        - method (PK)
        - window_type (PK)
        - average_pocket_area_loss_per_second
    """
    df_metric = pd.DataFrame(df_play_pocket_metrics)
    df_metric["average_pocket_area_loss_per_second"] = df_metric.apply(
        lambda df: get_average_pocket_area_loss_per_second(
            area_start=df["area_start"],
            area_end=df["area_end"],
            time_start=df["time_start"],
            time_end=df["time_end"],
        ),
        axis=1,
    )
    return df_metric


def get_play_pocket_metrics(df_area: pd.DataFrame) -> pd.DataFrame:
    """
    Parameters:
    df_area:
      Contains columns:
        - gameId (PK)
        - playId (PK)
        - frameId (PK)
        - method (PK)
        - window_type (PK)
        - area

    The input can contain as many types of time window as needed.

    Returns:
    Contains columns:
        - gameId (PK)
        - playId (PK)
        - method (PK)
        - window_type (PK)
        - median_area
        - average_area
        - area_start
        - area_end
        - time_start
        - time_end
    """
    # Copy input and add columns to mark start and end of time window.
    df = pd.DataFrame(df_area)
    # Find the first and last frame of each play.
    play_keys = ["gameId", "playId", "method", "window_type"]
    aggregations = {
        "min": ("frameId", min),
        "max": ("frameId", max),
        "median_area": ("area", np.median),
        "average_area": ("area", np.mean),
    }
    df_time_window = df.groupby(play_keys).agg(**aggregations).reset_index()
    """
    df_time_window =
    gameId  playId  method	window_type     min     max
    1       1       A       after_snap      5       25
    1       2       A       after_snap      2       22
    1       1       B       after_snap      5       25
    1       2       B       after_snap      2       22
    1       1       A       before_pass     ...
    ...
    """
    # Join in the start pocket area for each play.
    # Note: The join should explode if there are multiple `method` rows, so that we get each of them.
    # Note: The join columns have different names on each side.
    window_cols = ["median_area", "average_area"]
    start_cols = ["frameId", "min", "max", "area_start"]
    all_start_cols = play_keys + window_cols + start_cols
    df_with_start = df_time_window.merge(
        df,
        left_on=(play_keys + ["min"]),
        right_on=(play_keys + ["frameId"]),
        how="left",
    ).rename(columns={"area": "area_start"})[all_start_cols]
    # Join in the end pocket area for each play.
    df_with_both = (
        df_with_start.merge(
            df,
            left_on=(play_keys + ["max"]),
            right_on=(play_keys + ["frameId"]),
            how="left",
        )
        .rename(columns={"area": "area_end"})
        .drop(columns=["frameId_x", "frameId_y"])
    )
    """
    gameId	playId  method  window_type		min     max     area_start	area_end
    1       1       A       after_snap		5       25      100         80
    1       2       A       after_snap		2       22      120         95
    1       1       B       after_snap		5       25      20          12
    1       2       B       after_snap		2       22      23          20
    1       1       A       before_pass		...
    ...
    """
    frames_per_second = 10.0
    df_with_both["time_start"] = (
        df_with_both["min"].astype(float) / frames_per_second
    )
    df_with_both["time_end"] = (
        df_with_both["max"].astype(float) / frames_per_second
    )
    drop_cols = ["min", "max"]
    df_with_both.drop(columns=drop_cols, inplace=True)
    return df_with_both
