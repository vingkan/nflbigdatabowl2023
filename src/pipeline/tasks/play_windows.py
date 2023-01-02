import pandas as pd


def get_frames_for_time_windows(
    df_events: pd.DataFrame, df_areas: pd.DataFrame, window_size_frames: int
) -> pd.DataFrame:
    # This method will apply all the area algorithms to the dataframe and filter out plays
    """
    Parameters:
    df_events:
      Contains columns:
        - gameId (PK)
        - playId (PK)
        - frameId (PK)
        - event
        - frame_start (snap of the ball)
        - frame_end (pass, sack, etc)
        - passer_out_of_pocket
        - elgible_for_pocket

    df_areas:
        Contains columns:
        - gameId (PK)
        - playId (PK)
        - frameId (PK)
        - method (PK)
        - pocket
        - area

    second_factor:
        -X seconds factor after snap/before snap

    The input can contain as many types of time window as needed.
    For example:
    - window_type = `x_after_snap`:
        - Already filtered out frames before the snap.
        - Already filtered out any plays that end less than X seconds after snap.
    - window_type = `x_before_pass`:
        - Already filtered out frames earlier than X seconds before pass.
        - Already filtered out frames after pass.
        - Already filtered out any plays where the pass is less than X seconds after the snapp

    Returns:
    Contains columns:
        - gameId (PK)
        - playId (PK)
        - frameId (PK)
        - method (PK)
        - window_type (PK)
        - pocket
        - area
    """
    df = pd.DataFrame(df_events)

    # join to add frame where pass happened
    df_pass = df.query("event == 'pass_forward'")[
        ["gameId", "playId", "frameId"]
    ].rename(columns={"frameId": "pass_frame"})
    df = df.merge(df_pass, how="left", on=["gameId", "playId"])

    df["frames_elapsed"] = df["frameId"] - df["frame_start"]
    df["window_size"] = window_size_frames
    df["total_frames"] = df["frame_end"] - df["frame_start"]

    # this is not the frame immediately before the pass, this is the frame factor before the pass frame
    df["frame_before_pass"] = df["pass_frame"] - window_size_frames

    # Bandit thinks that strings with "pass" are passwords, so we have to tell
    # it that these queries are safe with `nosec`.
    query_x_before_pass = (  # nosec
        "pass_frame == pass_frame "
        "and frameId <= pass_frame "
        "and frameId >= frame_before_pass "
        "and frame_before_pass >= frame_start "
    )
    df_before_pass = pd.DataFrame(df.query(query_x_before_pass))
    df_before_pass["window_type"] = "before_pass"  # nosec

    query_x_after_snap = (
        "frameId >= frame_start "
        "and frames_elapsed <= window_size "
        "and total_frames >= window_size "
    )
    df_after_snap = pd.DataFrame(df.query(query_x_after_snap))
    df_after_snap["window_type"] = "after_snap"

    df_windows = pd.concat([df_after_snap, df_before_pass])

    df_out = df_windows.merge(
        df_areas, on=["gameId", "playId", "frameId"], how="left"
    )

    return df_out
