import pandas as pd

from src.pipeline.tasks.constants import (
    PFF_PRIMARY_KEY,
    PLAY_PRIMARY_KEY,
    TRACKING_PRIMARY_KEY,
)

FIELD_LENGTH = 120
FIELD_WIDTH = 53 + (1.0 / 3.0)


def align_coordinates(direction: str, x: float, y: float) -> pd.Series:
    """
    Returns a new row with three columns so that the coordinates and play
    direction always go right.
    """
    if direction == "right":
        new_x = x
        new_y = y
    elif direction == "left":
        # Rotate coordinates by 180 degrees, then shift by the length and width
        # of the football field.
        new_x = (-1 * x) + FIELD_LENGTH
        new_y = (-1 * y) + FIELD_WIDTH
    else:
        raise ValueError(f"Invalid direction: {direction}")

    new_direction = "right"
    return pd.Series([new_direction, new_x, new_y])


def rotate_coordinates(x: float, y: float) -> pd.Series:
    """
    Returns a new row with two columns so that the coordinates have the length
    of the field on the y-axis and the width of the field on the x-axis. On the
    x-axis, the left sideline is 0 and the right sideline is 53.333. On the
    y-axis, the bottom endline is 0 and the top endline is 120.
    """
    # x-coordinate takes the value of the y-coordinate, but also needs to reset
    # the axis to run from 0 to 53.333 instead of from 53.333 to 0.
    new_x = FIELD_WIDTH - y
    # y-coordinate just takes the value of the x-coordinate.
    new_y = x
    return pd.Series([new_x, new_y])


def align_tracking_data(df_tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns tracking data so that all plays have `playDirection = right`.
    """
    # Copy input DataFrame.
    df = pd.DataFrame(df_tracking)
    df[["playDirection", "x", "y"]] = df.apply(
        lambda row: align_coordinates(
            direction=row["playDirection"],
            x=row["x"],
            y=row["y"],
        ),
        axis=1,
    )
    return df


def rotate_tracking_data(df_tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Rotates tracking data so that the x-axis is the width of the football field
    and the y-axis is the length of the football field.

    Tracking data should already be aligned.
    """
    # Copy input DataFrame.
    df = pd.DataFrame(df_tracking)
    df[["x", "y"]] = df.apply(
        lambda row: rotate_coordinates(x=row["x"], y=row["y"]),
        axis=1,
    )
    return df


def transform_to_tracking_display(
    df_tracking: pd.DataFrame, df_plays: pd.DataFrame, df_pff: pd.DataFrame
) -> pd.DataFrame:
    """
    Transforms tracking data and joins to other datasets to produce the format
    needed to display in visualiations.
    """
    tracking_required_columns = TRACKING_PRIMARY_KEY + [
        "jerseyNumber",
        "team",
        "event",
        "x",
        "y",
        "o",
        "dir",
    ]
    plays_required_columns = PLAY_PRIMARY_KEY + [
        "possessionTeam",
    ]
    pff_required_columns = PFF_PRIMARY_KEY + ["pff_role"]
    df_plays_minimal = df_plays[plays_required_columns]
    df_pff_minimal = df_pff[pff_required_columns]
    df_tracking_minimal = df_tracking[tracking_required_columns]

    # Join selected columns from each dataframe
    df_join = df_tracking_minimal.merge(
        df_plays_minimal, on=PLAY_PRIMARY_KEY, how="left"
    ).merge(df_pff_minimal, on=PFF_PRIMARY_KEY, how="left")

    # Transform columns for final dataframe
    df_join["jerseyNumber"] = df_join["jerseyNumber"].fillna(0).astype(int)
    df_join["jerseyNumber"] = df_join["jerseyNumber"].astype(str)
    df_join["object_id"] = df_join["team"] + " " + df_join["jerseyNumber"]
    df_join["pff_role"] = df_join["pff_role"].fillna("Football")
    return df_join
