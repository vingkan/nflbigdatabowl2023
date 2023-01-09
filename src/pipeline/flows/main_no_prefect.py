from src.metrics.pocket_area.all import POCKET_AREA_METHODS
from src.pipeline.tasks import (
    align_tracking_data,
    augment_tracking_events,
    calculate_average_pocket_area_loss_per_second,
    calculate_pocket_area,
    center_tracking_data,
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

DEFAULT_INPATH = "/workspace/nflbigdatabowl2023/data/raw"
DEFAULT_OUTPATH = "/workspace/nflbigdatabowl2023/data/outputs"


def main_flow(**kwargs):
    # Get flow parameters.
    inpath = kwargs.get("inpath", DEFAULT_INPATH)
    outpath = kwargs.get("outpath", DEFAULT_OUTPATH)
    # Maximum number of weeks to process. If None, process all.
    max_weeks = kwargs.get("max_weeks", 8)
    # Maximum number of games to process. If None, process all.
    max_games = kwargs.get("max_games", None)
    # Maximum number of plays per game to process. If None, process all.
    max_plays = kwargs.get("max_plays", None)
    # How far the passer can go along the field width from the ball snap to be
    # considered in the officiating pocket area.
    max_yards_from_snap = kwargs.get("max_yards_from_snap", 7)
    # How many frames to include in the time windows (e.g. x_after_snap,
    # x_before_pass). For example, 20 frames leads to 2 second windows.
    window_size_frames = kwargs.get("window_size_frames", 20)

    # Read raw data.
    df_pff = read_csv(f"{inpath}/pffScoutingData.csv")
    df_plays = read_csv(f"{inpath}/plays.csv")
    df_tracking_all = read_tracking_data(f"{inpath}/week", weeks=max_weeks)

    # Limit to max weeks, games, and plays per game, if requested.
    df_tracking_games = limit_by_child_keys(
        df_tracking_all,
        parent_keys=["week"],
        child_keys=["gameId"],
        n=max_games,
    )
    df_tracking_limited = limit_by_child_keys(
        df_tracking_games,
        parent_keys=["gameId"],
        child_keys=["playId"],
        n=max_plays,
    )

    # Align and rotate tracking data.
    df_tracking_aligned = align_tracking_data(df_tracking_limited)
    df_tracking_rotated = rotate_tracking_data(df_tracking_aligned)

    # Find frames where the passer has left the possible pocket area.
    # Requires actual yard lines, which means we must use the aligned and
    # rotated tracking data, before centering is applied.
    df_passer_out_of_pocket = get_passer_out_of_pocket(
        df_tracking_rotated, df_pff, max_yards_from_snap
    )

    # Process event data: clean events, add pocket eligibility data, and join
    # back to tracking data.
    df_clean_events = clean_event_data(df_tracking_limited)
    df_events = get_pocket_eligibility(df_clean_events, df_passer_out_of_pocket)
    df_tracking_with_events = augment_tracking_events(
        df_tracking_rotated, df_events
    )

    # Center tracking data on ball snap point so that all spatial logic has the
    # same origin and coordinate system.
    # Must come after augmenting with event data to get the clean event names.
    df_tracking = center_tracking_data(df_tracking_with_events)

    # Transform tracking data to display format.
    df_tracking_display = transform_to_tracking_display(
        df_tracking, df_plays, df_pff
    )

    # Transform raw tracking data to frame records.
    df_frames = transform_to_frames(df_tracking, df_pff)
    df_frame_records = transform_to_records_per_frame(df_frames)

    # Run each pocket area calculation function and combine results.
    area_methods = list(POCKET_AREA_METHODS.items())
    df_area_list = [
        calculate_pocket_area(df_frame_records, method)
        for method in area_methods
    ]
    df_areas = union_dataframes(df_area_list)

    # Calculate metrics for each play.
    df_windows_with_area = get_frames_for_time_windows(
        df_events, df_areas, window_size_frames=window_size_frames
    )
    df_play_pocket_metrics = get_play_pocket_metrics(df_windows_with_area)
    df_play_metrics = calculate_average_pocket_area_loss_per_second(
        df_play_pocket_metrics
    )

    # Write outputs to disk.
    write_csv(df_tracking_display, f"{outpath}/tracking_display.csv")
    write_csv(df_events, f"{outpath}/events.csv")
    write_csv(df_areas, f"{outpath}/pocket_areas.csv")
    write_csv(df_play_metrics, f"{outpath}/play_metrics.csv")
