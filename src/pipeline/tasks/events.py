from typing import Optional

import pandas as pd


def clean_autoevent(raw: str) -> Optional[str]:
    # Replace `None` event with null values.
    if raw == "None":
        return None

    # Rename auto event names to base event names.
    autoevent_renames = {
        "autoevent_ballsnap": "ball_snap",
        "autoevent_passforward": "pass_forward",
        "autoevent_passinterrupted": "pass_interrupted",
    }
    # If the raw name is not in the dictionary, fall back
    # to the raw name itself.
    renamed_event = autoevent_renames.get(raw, raw)
    return renamed_event


def remove_redundant_event(
    event: Optional[str], is_first: bool
) -> Optional[str]:
    # For example, a play could have multiple `fumble` events, so we only want to
    # remove redundant events that are non-repeatable.
    non_repeatable_events = {"ball_snap", "pass_forward"}
    should_not_repeat = event in non_repeatable_events
    is_repeat = not is_first
    if should_not_repeat and is_repeat:
        return None
    return event


def clean_event_data(df_tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Parameters:
        df_tracking: DataFrame of raw tracking data for many plays.

    Returns:
        DataFrame of cleaned events for each play:
        Columns:
        - gameId
        - playId
        - frameId
        - event (Optional[str]): Cleaned event name, without redundant events.

    The cleaned event name:
    - No longer has auto event names
    - No longer has redundant events (e.g. only one `ball_snap` per play)
    """
    # Get only columns for event per frame, also copies the DataFrame.
    base_columns = ["gameId", "playId", "frameId", "event"]
    df = df_tracking[base_columns].drop_duplicates()
    df["clean_event"] = df["event"].apply(clean_autoevent)

    # Find first frame for each event type.
    df_event_first_frame = (
        df.groupby(["gameId", "playId", "clean_event"])
        .agg(**{"first_frame": ("frameId", min)})
        .reset_index()
    )
    df_with_first = df.merge(
        df_event_first_frame,
        left_on=["gameId", "playId", "clean_event", "frameId"],
        right_on=["gameId", "playId", "clean_event", "first_frame"],
        how="left",
    )
    df_with_first["is_first_event_of_type"] = df_with_first[
        "first_frame"
    ].notna()

    # Set redundant events to a null value.
    df_with_first["clean_event"] = df_with_first.apply(
        lambda row: remove_redundant_event(
            event=row["clean_event"],
            is_first=row["is_first_event_of_type"],
        ),
        axis=1,
    )

    # Rename `clean_event` to `event` and drop unnecessary columns.
    df_with_first["event"] = df_with_first["clean_event"]
    drop_columns = ["first_frame", "is_first_event_of_type", "clean_event"]
    df_with_first.drop(columns=drop_columns, inplace=True)
    return df_with_first


def augment_tracking_events(
    df_tracking: pd.DataFrame, df_events: pd.DataFrame
) -> pd.DataFrame:
    """
    Copies the tracking DataFrame and replaces the `event` column with the
    cleaned event for that frame.
    Also new columns from event data, such as `frame_start` and `frame_end`.
    """
    # Returns a copy of the DataFrame without the old event column.
    df_base = df_tracking.drop(columns=["event"])
    df_with_event = df_base.merge(df_events, on=["gameId", "playId", "frameId"])
    return df_with_event
