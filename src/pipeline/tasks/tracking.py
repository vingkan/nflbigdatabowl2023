import pandas as pd

from src.pipeline.tasks.constants import (
    PFF_PRIMARY_KEY,
    PLAY_PRIMARY_KEY,
    TRACKING_PRIMARY_KEY,
)


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
