from prefect import flow, task, unmapped

from src.metrics.pocket_area.all import POCKET_AREA_METHODS
from src.pipeline.tasks import (
    calculate_pocket_area,
    limit_by_child_keys,
    limit_by_keys,
    read_csv,
    transform_to_frames,
    transform_to_records_per_frame,
    transform_to_tracking_display,
    union_dataframes,
    write_csv,
)

DATA_DIR = "/workspace/nflbigdatabowl2023/data"


@flow
def main_flow(**kwargs):
    # Get flow parameters.
    # Maximum number of games to process. If None, process all.
    max_games = kwargs.get("max_games")
    # Maximum number of plays per game to process. If None, process all.
    max_plays = kwargs.get("max_plays")

    # Read raw data.
    df_pff = task(read_csv)(f"{DATA_DIR}/raw/pffScoutingData.csv")
    df_plays = task(read_csv)(f"{DATA_DIR}/raw/plays.csv")
    df_tracking_all = task(read_csv)(f"{DATA_DIR}/raw/week1.csv")

    # Limit to max games and plays per game, if requested.
    df_tracking_games = limit_by_keys(
        df_tracking_all, keys=["gameId"], n=max_games
    )
    df_tracking = limit_by_child_keys(
        df_tracking_games,
        parent_keys=["gameId"],
        child_keys=["playId"],
        n=max_plays,
    )

    # TODO(vinesh): Align, rotate, and orient tracking data.

    # Transform tracking data to display format.
    df_tracking_display = task(transform_to_tracking_display)(
        df_tracking, df_plays, df_pff
    )

    # Transform raw tracking data to frame records.
    df_frames = task(transform_to_frames)(df_tracking, df_pff)
    df_frame_records = task(transform_to_records_per_frame)(df_frames)

    # Run each pocket area calculation function and combine results.
    area_methods = list(POCKET_AREA_METHODS.items())
    df_area_list = task(calculate_pocket_area).map(
        unmapped(df_frame_records), area_methods
    )
    df_areas = task(union_dataframes)(df_area_list)

    # Write outputs to disk.
    task(write_csv)(
        df_tracking_display, f"{DATA_DIR}/outputs/tracking_display.csv"
    )
    task(write_csv)(df_frames, f"{DATA_DIR}/outputs/frames.csv")
    task(write_csv)(df_frame_records, f"{DATA_DIR}/outputs/frame_records.csv")
    task(write_csv)(df_areas, f"{DATA_DIR}/outputs/pocket_areas.csv")
