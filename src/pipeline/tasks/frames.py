from typing import Dict, List

import pandas as pd

from src.metrics.pocket_area.base import PocketRole
from src.metrics.pocket_area.helpers import convert_pff_role_to_pocket_role
from src.pipeline.tasks.constants import (
    FRAME_PRIMARY_KEY,
    PFF_PRIMARY_KEY,
    TRACKING_PRIMARY_KEY,
)

FRAME_COLUMNS = ["x", "y", "role"]


def get_records_for_frame(df_group: pd.DataFrame) -> List[Dict]:
    """Converts the frame tracking records into a list of dictionaries."""
    return df_group[FRAME_COLUMNS].to_dict(orient="records")


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
    df_grouped = df_frames.groupby(FRAME_PRIMARY_KEY)
    df_frame_records = df_grouped.apply(get_records_for_frame)
    return df_frame_records.reset_index().rename(columns={0: "records"})
