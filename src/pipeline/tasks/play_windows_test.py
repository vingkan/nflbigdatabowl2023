import pandas as pd

from src.pipeline.tasks.play_windows import get_frames_for_time_windows
from src.pipeline.tasks.test_helpers import row_creator


def test_get_frames_for_time_windows():
    # Helper function to create event input rows.
    event_columns = [
        "gameId",
        "playId",
        "frameId",
        "event",
        "frame_start",
        "frame_end",
    ]
    event_row = row_creator(event_columns)
    df_events = pd.DataFrame(
        [
            event_row(1, 1, 1, None, 2, 38),
            event_row(1, 1, 2, "ball_snap", 2, 38),
            event_row(1, 1, 11, None, 2, 38),
            event_row(1, 1, 12, None, 2, 38),
            event_row(1, 1, 13, None, 2, 38),
            event_row(1, 1, 27, None, 2, 38),
            event_row(1, 1, 28, None, 2, 38),
            event_row(1, 1, 29, None, 2, 38),
            event_row(1, 1, 38, "pass_forward", 2, 38),
            # Exclude plays that are shorter than the time window.
            event_row(2, 2, 1, "ball_snap", 1, 4),
            event_row(2, 2, 4, "pass_forward", 1, 4),
        ]
    )

    # Helper function to create area input rows.
    area_columns = ["gameId", "playId", "frameId", "method", "pocket", "area"]
    area_row = row_creator(area_columns)
    df_areas = pd.DataFrame(
        [
            area_row(1, 1, 1, "A", "(pocket a)", 100),
            area_row(1, 1, 2, "A", "(pocket a)", 90),
            area_row(1, 1, 11, "A", "(pocket a)", 80),
            area_row(1, 1, 12, "A", "(pocket a)", 70),
            area_row(1, 1, 13, "A", "(pocket a)", 60),
            area_row(1, 1, 27, "A", "(pocket a)", 50),
            area_row(1, 1, 28, "A", "(pocket a)", 40),
            area_row(1, 1, 29, "A", "(pocket a)", 30),
            area_row(1, 1, 38, "A", "(pocket a)", 20),
            area_row(1, 1, 1, "B", "(pocket b)", 10),
            area_row(1, 1, 2, "B", "(pocket b)", 9),
            area_row(1, 1, 11, "B", "(pocket b)", 8),
            area_row(1, 1, 12, "B", "(pocket b)", 7),
            area_row(1, 1, 13, "B", "(pocket b)", 6),
            area_row(1, 1, 27, "B", "(pocket b)", 5),
            area_row(1, 1, 28, "B", "(pocket b)", 4),
            area_row(1, 1, 29, "B", "(pocket b)", 3),
            area_row(1, 1, 38, "B", "(pocket b)", 2),
        ]
    )

    # Run actual transformation.
    actual = get_frames_for_time_windows(
        df_events, df_areas, window_size_frames=10
    )

    # Sort actual rows and transform to list of dictionaries.
    sort_cols = ["gameId", "playId", "window_type", "method", "frameId"]
    actual_rows = actual.sort_values(sort_cols).to_dict(orient="records")

    # Helper function to create output rows.
    output_columns = [
        "gameId",
        "playId",
        "frameId",
        "window_type",
        "method",
        "pocket",
        "area",
        "frame_start",
        "frame_end",
    ]
    output_row = row_creator(output_columns)
    expected = [
        # Filter to only plays 10 frames after snap.
        output_row(1, 1, 2, "after_snap", "A", "(pocket a)", 90, 2, 38),
        output_row(1, 1, 11, "after_snap", "A", "(pocket a)", 80, 2, 38),
        output_row(1, 1, 12, "after_snap", "A", "(pocket a)", 70, 2, 38),
        # Handle multiple pocket area methods.
        output_row(1, 1, 2, "after_snap", "B", "(pocket b)", 9, 2, 38),
        output_row(1, 1, 11, "after_snap", "B", "(pocket b)", 8, 2, 38),
        output_row(1, 1, 12, "after_snap", "B", "(pocket b)", 7, 2, 38),
        # When the pocket ends due to a pass, before_end matches before_pass.
        output_row(1, 1, 28, "before_end", "A", "(pocket a)", 40, 2, 38),
        output_row(1, 1, 29, "before_end", "A", "(pocket a)", 30, 2, 38),
        output_row(1, 1, 38, "before_end", "A", "(pocket a)", 20, 2, 38),
        output_row(1, 1, 28, "before_end", "B", "(pocket b)", 4, 2, 38),
        output_row(1, 1, 29, "before_end", "B", "(pocket b)", 3, 2, 38),
        output_row(1, 1, 38, "before_end", "B", "(pocket b)", 2, 2, 38),
        # Filter to only plays 10 frames before pass.
        output_row(1, 1, 28, "before_pass", "A", "(pocket a)", 40, 2, 38),
        output_row(1, 1, 29, "before_pass", "A", "(pocket a)", 30, 2, 38),
        output_row(1, 1, 38, "before_pass", "A", "(pocket a)", 20, 2, 38),
        # Handle multiple pocket area methods.
        output_row(1, 1, 28, "before_pass", "B", "(pocket b)", 4, 2, 38),
        output_row(1, 1, 29, "before_pass", "B", "(pocket b)", 3, 2, 38),
        output_row(1, 1, 38, "before_pass", "B", "(pocket b)", 2, 2, 38),
        # No rows for game 2, play 2 since it is shorter than the time window.
    ]
    assert actual_rows == expected
