from prefect import flow, task, unmapped

from src.metrics.pocket_area.all import POCKET_AREA_METHODS
from src.pipeline.tasks import (
    align_tracking_data,
    augment_tracking_events,
    calculate_average_pocket_area_loss_per_second,
    calculate_pocket_area,
    clean_event_data,
    get_frames_for_time_windows,
    get_passer_out_of_pocket,
    get_play_pocket_metrics,
    get_pocket_eligibility,
    limit_by_child_keys,
    limit_by_keys,
    read_csv,
    read_tracking_data,
    rotate_tracking_data,
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
    # Maximum number of weeks to process. If None, process all.
    max_weeks = kwargs.get("max_weeks") or 8
    # Maximum number of games to process. If None, process all.
    max_games = kwargs.get("max_games")
    # Maximum number of plays per game to process. If None, process all.
    max_plays = kwargs.get("max_plays")
    # How far the passer can go along the field width from the ball snap to be
    # considered in the officiating pocket area.
    max_yards_from_snap = 7
    # How many frames to include in the time windows (e.g. x_after_snap,
    # x_before_pass). For example, 20 frames leads to 2 second windows.
    window_size_frames = 20

    # Read raw data.
    df_pff = task(read_csv)(f"{DATA_DIR}/raw/pffScoutingData.csv")
    df_plays = task(read_csv)(f"{DATA_DIR}/raw/plays.csv")
    df_tracking_all = task(read_tracking_data)(
        f"{DATA_DIR}/raw/week", weeks=max_weeks
    )

    # Limit to max weeks, games, and plays per game, if requested.
    df_tracking_games = task(limit_by_child_keys)(
        df_tracking_all,
        parent_keys=["week"],
        child_keys=["gameId"],
        n=max_games,
    )
    df_tracking_limited = task(limit_by_child_keys)(
        df_tracking_games,
        parent_keys=["gameId"],
        child_keys=["playId"],
        n=max_plays,
    )

    # Align and rotate tracking data.
    df_tracking_aligned = task(align_tracking_data)(df_tracking_limited)
    df_tracking_rotated = task(rotate_tracking_data)(df_tracking_aligned)

    # Find frames where the passer has left the possible pocket area.
    df_passer_out_of_pocket = task(get_passer_out_of_pocket)(
        df_tracking_rotated, df_pff, max_yards_from_snap
    )

    # Process event data: clean events, add pocket eligibility data, and join
    # back to tracking data.
    df_clean_events = task(clean_event_data)(df_tracking_limited)
    df_events = task(get_pocket_eligibility)(
        df_clean_events, df_passer_out_of_pocket
    )
    df_tracking = task(augment_tracking_events)(df_tracking_rotated, df_events)

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

    # Calculate metrics for each play.
    df_windows_with_area = task(get_frames_for_time_windows)(
        df_events, df_areas, window_size_frames=window_size_frames
    )
    df_play_pocket_metrics = task(get_play_pocket_metrics)(df_windows_with_area)
    df_play_metrics = task(calculate_average_pocket_area_loss_per_second)(
        df_play_pocket_metrics
    )

    # Write outputs to disk.
    task(write_csv)(
        df_tracking_display, f"{DATA_DIR}/outputs/tracking_display.csv"
    )
    task(write_csv)(df_events, f"{DATA_DIR}/outputs/events.csv")
    task(write_csv)(df_areas, f"{DATA_DIR}/outputs/pocket_areas.csv")
    task(write_csv)(df_play_metrics, f"{DATA_DIR}/outputs/play_metrics.csv")
