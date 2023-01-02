import pandas as pd

from src.metrics.pocket_area.base import PocketRole
from src.metrics.pocket_area.helpers import convert_pff_role_to_pocket_role
from src.pipeline.tasks.constants import (
    FRAME_PRIMARY_KEY,
    PFF_PRIMARY_KEY,
    TRACKING_PRIMARY_KEY,
)

FRAME_COLUMNS = ["x", "y", "role"]


def transform_to_frames(
    df_tracking: pd.DataFrame, df_pff: pd.DataFrame
) -> pd.DataFrame:
    """Transforms tracking data to pull in the data needed for each frame."""
    # Join tracking data to PFF data to get player roles
    df_frames_joined = df_tracking.merge(df_pff, on=PFF_PRIMARY_KEY, how="left")

    # Convert PFF role to pocket role
    df_frames_joined["pff_role"] = df_frames_joined["pff_role"].fillna(
        "Football"
    )
    df_frames_joined["role"] = df_frames_joined["pff_role"].apply(
        convert_pff_role_to_pocket_role
    )
    unique_pocket_roles = set(df_frames_joined["role"].unique())
    if unique_pocket_roles == {PocketRole.UNKNOWN.value}:
        message = "Pocket role conversion failed: only got `unknown` role."
        raise ValueError(message)

    # Select and return columns
    df_frames = df_frames_joined[TRACKING_PRIMARY_KEY + FRAME_COLUMNS]
    return df_frames


def transform_to_records_per_frame(df_frames: pd.DataFrame) -> pd.DataFrame:
    """Aggregates the data for each frame into one row per frame."""
    # Copy input.
    df = pd.DataFrame(df_frames)
    # Zip columns needed for each object into a new column.
    # If you want to expose a new column to the pocket area functions, you must
    # add it here.
    df["object"] = [
        {"x": x, "y": y, "role": role}
        for x, y, role in zip(df["x"], df["y"], df["role"])
    ]
    # Aggregate objects into a list for each frame.
    df_grouped = df.groupby(FRAME_PRIMARY_KEY)
    df_out = df_grouped.agg(records=("object", list)).reset_index()
    return df_out
