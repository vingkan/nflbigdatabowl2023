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

    def has_passer_out_of_pocket(row: pd.Series) -> bool:
        x_delta = abs(row["passer_x"] - row["ball_snap_x"])
        return x_delta > max_yards_from_snap

    df["passer_out_of_pocket"] = df.apply(has_passer_out_of_pocket, axis=1)

    # Drop unnecessary columns and return result.
    drop_columns = ["ball_snap_x", "passer_x"]
    df.drop(columns=drop_columns, inplace=True)
    return df


def is_eligible_for_pocket(row: pd.Series) -> bool:
    """Determines whether the given frame could have a pocket."""
    first_pocket_frame = row["frame_start"]
    last_pocket_frame = row["frame_end"]
    frame_id = row["frameId"]
    has_passer_out_of_pocket = row["passer_out_of_pocket"]

    if pd.isna(has_passer_out_of_pocket):
        raise ValueError("Null `passer_out_of_pocket`. Join may have failed.")

    # If passer is outside the officiating pocket area, pocket is not eligible.
    if has_passer_out_of_pocket:
        return False

    # If there was no first pocket frame, the pocket is never eligible.
    if pd.isna(first_pocket_frame):
        return False

    # If there was no last pocket frame, the pocket is eligible starting from
    # the first frame.
    if pd.isna(last_pocket_frame):
        return frame_id >= first_pocket_frame

    # Otherwise, pocket is eligible between the first and last frame, inclusive.
    return first_pocket_frame <= frame_id <= last_pocket_frame


def get_pocket_eligibility(
    df_events: pd.DataFrame,
    df_passer_out_of_pocket: pd.DataFrame,
    keep_intermediate_columns: bool = False,
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
        keep_intermediate_columns: Whether or not to keep columns used to
            calculate eligibility.
    Returns:
        DataFrame with new column to indicate which frames could have a pocket.
            Columns:
            - gameId
            - playId
            - frameId
            - event
            - eligible_for_pocket
    """
    play_keys = ["gameId", "playId"]

    # Get the frame where the pocket eligibility starts for each play.
    df_start = (
        df_events.query("event == 'ball_snap'")
        .groupby(play_keys)
        .agg(**{"frame_start": ("frameId", min)})
        .reset_index()
    )

    # Get the frame where the pocket eligibility ends for each play.
    # TODO(vinesh): Check if there are new types of events in the later weeks of
    # data that could end pocket eligibility.
    pocket_ending_events = {
        "fumble",
        "handoff",
        "lateral",
        "pass_forward",
        "qb_sack",
        "qb_strip_sack",
        "run",
    }
    ending_events = ", ".join([f"'{e}'" for e in pocket_ending_events])
    end_query = f"event in ({ending_events})"
    df_end = (
        df_events.query(end_query)
        .groupby(play_keys)
        .agg(**{"frame_end": ("frameId", min)})
        .reset_index()
    )

    # Join start and end frames to main DataFrame, also join in passer out of
    # pocket indicator for each frame.
    df = (
        df_events.merge(df_start, on=play_keys, how="left")
        .merge(df_end, on=play_keys, how="left")
        .merge(df_passer_out_of_pocket, on=play_keys + ["frameId"], how="left")
    )

    # Determine pocket eligibility.
    df["eligible_for_pocket"] = df.apply(is_eligible_for_pocket, axis=1)
    if not keep_intermediate_columns:
        drop_columns = ["frame_start", "frame_end", "passer_out_of_pocket"]
        df.drop(columns=drop_columns, inplace=True)
    return df
