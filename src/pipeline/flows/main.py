from prefect import flow, task, unmapped

from src.metrics.pocket_area.all import POCKET_AREA_METHODS
from src.pipeline.tasks import (
    calculate_pocket_area,
    limit_by_keys,
    read_csv,
    transform_to_frames,
    transform_to_records_per_frame,
    union_dataframes,
    write_csv,
)

DEFAULT_DATA_DIR = "/workspace/nflbigdatabowl2023/data"

PLAY_PRIMARY_KEY = ["gameId", "playId"]


@flow
def main_flow(**kwargs):
    # Get flow parameters
    max_plays = kwargs.get("max_plays")

    # Read raw data
    df_pff = task(read_csv)(f"{DEFAULT_DATA_DIR}/raw/pffScoutingData.csv")
    df_tracking_all = task(read_csv)(f"{DEFAULT_DATA_DIR}/raw/week1.csv")

    # Limit to max plays, if requested
    df_tracking = limit_by_keys(df_tracking_all, PLAY_PRIMARY_KEY, max_plays)
    # TODO(vinesh): Align, rotate, and orient tracking data.

    # Transform raw tracking data to frame records
    df_frames = task(transform_to_frames)(df_tracking, df_pff)
    df_frame_records = task(transform_to_records_per_frame)(df_frames)

    # Run each pocket area calculation function and combine results
    area_methods = list(POCKET_AREA_METHODS.items())
    df_area_list = task(calculate_pocket_area).map(
        unmapped(df_frame_records), area_methods
    )
    df_areas = task(union_dataframes)(df_area_list)

    # Write outputs
    task(write_csv)(df_areas, f"{DEFAULT_DATA_DIR}/outputs/pocket_areas.csv")
