import numpy as np
import pandas as pd


def get_passer_out_of_pocket(
    df_tracking: pd.DataFrame, df_pff: pd.DataFrame, max_yards_from_snap: int
) -> pd.DataFrame:
    """
    Parameters:
        df_tracking: DataFrame with tracking data, already aligned and rotated.
        df_pff: DataFrame with raw PFF scouting data.
        max_yards_from_snap: Maximum number of yards to either side the passer
            can be from the location where the ball was snapped to be considered
            inside the officiating pocket area.

    Returns: DataFrame with an indicator for whether or not the passer is
        outside of the box that officiating crews might consider to be the
        maximum box that could contain the pocket.
        Columns:
        - gameId
        - playId
        - frameId
        - passer_out_of_pocket
    """
    # Get ball x-coordinate at snap.
    snap_columns = ["gameId", "playId", "x"]
    snap_filter_columns = ["event", "team"]
    df_snap = (
        df_tracking[snap_columns + snap_filter_columns]
        .query("event == 'ball_snap' and team == 'football'")
        .drop_duplicates()
        .drop(columns=snap_filter_columns)
        .rename(columns={"x": "ball_snap_x"})
    )

    # Get passer x-coordinate at each frame.
    passer_columns = ["gameId", "playId", "frameId", "x"]
    passer_filter_columns = ["pff_role"]
    df_passer = (
        df_tracking.merge(df_pff, on=["gameId", "playId", "nflId"], how="left")[
            passer_columns + passer_filter_columns
        ]
        .query("pff_role == 'Pass'")
        .drop(columns=passer_filter_columns)
        .rename(columns={"x": "passer_x"})
    )

    # Join tracking data to ball snap and passer coordinates.
    tracking_columns = ["gameId", "playId", "frameId"]
    df = (
        df_tracking[tracking_columns]
        .drop_duplicates()
        .merge(df_snap, on=["gameId", "playId"], how="left")
        .merge(df_passer, on=["gameId", "playId", "frameId"], how="left")
    )

    # Determine whether or not the passer has left the officiated pocket.
    df["passer_out_of_pocket"] = (
        np.abs(df["passer_x"] - df["ball_snap_x"]) > max_yards_from_snap
    ).astype(int)

    # Drop unnecessary columns and return result.
    drop_columns = ["ball_snap_x", "passer_x"]
    df.drop(columns=drop_columns, inplace=True)
    return df


def get_pocket_eligibility(
    df_events: pd.DataFrame, df_passer_out_of_pocket: pd.DataFrame
) -> pd.DataFrame:
    """
    Parameters:
        df_events: DataFrame of each frame and cleaned event.
            Columns:
            - gameId
            - playId
            - frameId
            - event
        df_passer_out_of_pocket: Passer out of pocket indicator per frame.
            Columns:
            - gameId
            - playId
            - frameId
            - passer_out_of_pocket

    Returns:
        DataFrame with new column to indicate which frames could have a pocket.
            Columns:
            - gameId
            - playId
            - frameId
            - event
            - frame_start
            - frame_end
    """
    play_keys = ["gameId", "playId"]

    # Find the maximum frame for each play.
    df_max = (
        df_events.groupby(play_keys)
        .agg(**{"frame_max": ("frameId", max)})
        .reset_index()
    )

    # Find the frame where the pocket eligibility starts for each play.
    df_start = (
        df_events.query("event == 'ball_snap'")
        .groupby(play_keys)
        .agg(**{"frame_start": ("frameId", min)})
        .reset_index()
    )
    # Join start and max frames, as well as passer out of pocket data, to event
    # data, to help compute end frames.
    df_with_start = (
        df_events.merge(df_start, on=play_keys, how="left")
        .merge(df_max, on=play_keys, how="left")
        .merge(df_passer_out_of_pocket, on=play_keys + ["frameId"], how="left")
    )

    # Get the frame where the pocket eligibility ends for each play.
    # TODO(vinesh): Handle edge cases where pocket can be re-established, such
    # as a botched snap followed by pass from pocket.
    pocket_ending_events = {
        "fumble",
        "handoff",
        "lateral",
        "pass_forward",
        "qb_sack",
        "qb_strip_sack",
        "run",
        "tackle",
        "out_of_bounds",
    }
    is_end_event = df_with_start["event"].isin(pocket_ending_events)
    is_after_start = df_with_start["frameId"] >= df_with_start["frame_start"]
    is_outside_pocket = df_with_start["passer_out_of_pocket"]
    is_max = df_with_start["frameId"] == df_with_start["frame_max"]
    # Is after snap AND (has ending event OR is max frame OR is outside pocket)
    is_pocket_end = is_after_start & (is_end_event | is_max | is_outside_pocket)

    # Find and join end frames to event data.
    df_end = (
        df_with_start[is_pocket_end]
        .groupby(play_keys)
        .agg(**{"frame_end": ("frameId", min)})
        .reset_index()
    )
    df = df_events.merge(df_start, on=play_keys, how="left").merge(
        df_end, on=play_keys, how="left"
    )

    # Fill plays with null start and end frames with None.
    df["frame_start"] = df["frame_start"].fillna(np.nan).replace([np.nan], None)
    df["frame_end"] = df["frame_end"].fillna(np.nan).replace([np.nan], None)

    return df
