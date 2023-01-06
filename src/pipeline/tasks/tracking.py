import pandas as pd

from src.pipeline.tasks.constants import (
    FIELD_LENGTH,
    FIELD_WIDTH,
    PFF_PRIMARY_KEY,
    PLAY_PRIMARY_KEY,
    TRACKING_PRIMARY_KEY,
)

MAX_DEGREES = 360


def align_tracking_data(df_tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Aligns tracking data so that all plays have `playDirection = right`.
    """
    # Copy input DataFrame.
    df = pd.DataFrame(df_tracking)

    # Create series with 1 if play needs to be aligned, 0 otherwise.
    is_unaligned_mask = (df["playDirection"] == "left").astype(int)

    # Align coordinates.
    # Returns reverse factor of -1 if unaligned, otherwise 1.
    reverse_if_unaligned = (-2 * is_unaligned_mask) + 1
    added_length_if_unaligned = FIELD_LENGTH * is_unaligned_mask
    added_width_if_unaligned = FIELD_WIDTH * is_unaligned_mask
    # Rotate coordinates by 180 degrees, then shift by the length and width of
    # the football field.
    df["x"] = (reverse_if_unaligned * df["x"]) + added_length_if_unaligned
    df["y"] = (reverse_if_unaligned * df["y"]) + added_width_if_unaligned

    # Align angles.
    # Adds 180 degrees if unaligned, otherwise 0 degrees.
    added_angle_if_unaligned = 180 * is_unaligned_mask
    # Rotate angle clockwise by 180 degrees and clip to range [0, 360].
    df["o"] = (df["o"] + added_angle_if_unaligned) % MAX_DEGREES
    df["dir"] = (df["dir"] + added_angle_if_unaligned) % MAX_DEGREES

    # Now, all plays move towards the right.
    df["playDirection"] = "right"
    return df


def rotate_tracking_data(df_tracking: pd.DataFrame) -> pd.DataFrame:
    """
    Rotates tracking data so that the x-axis is the width of the football field
    and the y-axis is the length of the football field.

    For angles, 0 degrees points to the top endline, 90 degrees points to the right sideline, and so on.

    Tracking data should already be aligned.
    """
    # Copy input DataFrame.
    df = pd.DataFrame(df_tracking)

    # Rotate coordinates.
    # Save copy of original coordinates before swapping and transforming.
    original_x = df["x"]
    original_y = df["y"]
    # x-coordinate takes the value of the y-coordinate, but also needs to reset
    # the axis to run from 0 to 53.333 instead of from 53.333 to 0.
    df["x"] = FIELD_WIDTH - original_y
    # y-coordinate just takes the value of the x-coordinate.
    df["y"] = original_x

    # Rotate angles.
    # Rotate angle counterclockwise by 90 degrees (which is the same as 270
    # degrees clockwise) and clip to range [0, 360].
    df["o"] = (df["o"] + 270) % MAX_DEGREES
    df["dir"] = (df["dir"] + 270) % MAX_DEGREES

    return df


def transform_to_tracking_display(
    df_tracking: pd.DataFrame, df_plays: pd.DataFrame, df_pff: pd.DataFrame
) -> pd.DataFrame:
    """
    Transforms tracking data and joins to other datasets to produce the format
    needed to display in visualiations.
    """
    tracking_required_columns = TRACKING_PRIMARY_KEY + [
        "week",
        "jerseyNumber",
        "team",
        "event",
        "x",
        "y",
        "o",
        "dir",
        "frame_start",
        "frame_end",
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
