import pandas as pd

from src.pipeline.tasks.play_metrics import (
    get_average_pocket_area_loss_per_second,
    get_play_pocket_metrics,
)
from src.pipeline.tasks.test_helpers import row_creator


def test_get_play_pocket_metrics():
    # Common attributes to make each row definiton shorter.
    p1 = {"gameId": 1, "playId": 1}
    p2 = {"gameId": 2, "playId": 2}
    after_snap = {"window_type": "after_snap"}
    before_pass = {"window_type": "before_pass"}

    # Create input data.
    df_area_with_window = pd.DataFrame(
        [
            # Frames inside window, but not outside window.
            {**p1, "frameId": 5, "method": "A", **after_snap, "area": 100},
            {**p1, "frameId": 6, "method": "A", **after_snap, "area": 120},
            {**p1, "frameId": 25, "method": "A", **after_snap, "area": 80},
            # Multiple pocket area methods.
            {**p1, "frameId": 5, "method": "B", **after_snap, "area": 20},
            {**p1, "frameId": 6, "method": "B", **after_snap, "area": 30},
            {**p1, "frameId": 25, "method": "B", **after_snap, "area": 12},
            # Multiple window types.
            {**p1, "frameId": 12, "method": "A", **before_pass, "area": 110},
            {**p1, "frameId": 32, "method": "A", **before_pass, "area": 75},
            {**p1, "frameId": 12, "method": "B", **before_pass, "area": 15},
            {**p1, "frameId": 32, "method": "B", **before_pass, "area": 8},
            # Multiple plays.
            {**p2, "frameId": 5, "method": "A", **after_snap, "area": 110},
            {**p2, "frameId": 6, "method": "A", **after_snap, "area": 130},
            {**p2, "frameId": 25, "method": "A", **after_snap, "area": 85},
            {**p2, "frameId": 5, "method": "B", **after_snap, "area": 25},
            {**p2, "frameId": 6, "method": "B", **after_snap, "area": 35},
            {**p2, "frameId": 25, "method": "B", **after_snap, "area": 17},
            {**p2, "frameId": 12, "method": "A", **before_pass, "area": 115},
            {**p2, "frameId": 32, "method": "A", **before_pass, "area": 80},
            {**p2, "frameId": 12, "method": "B", **before_pass, "area": 18},
            {**p2, "frameId": 32, "method": "B", **before_pass, "area": 12},
        ]
    )

    # Run actual transformation.
    actual = get_play_pocket_metrics(df_area_with_window)

    # Sort actual rows and convert to dictionaries.
    sort_columns = ["gameId", "playId", "method", "window_type"]
    actual_rows = actual.sort_values(sort_columns).to_dict(orient="records")

    # Helper function to create expected rows.
    expected_columns = [
        "gameId",
        "playId",
        "method",
        "window_type",
        "area_start",
        "area_end",
        "time_start",
        "time_end",
    ]
    make_row = row_creator(expected_columns)

    # Compare to expected output.
    expected = [
        make_row(1, 1, "A", "after_snap", 100, 80, 0.5, 2.5),
        make_row(1, 1, "A", "before_pass", 110, 75, 1.2, 3.2),
        make_row(1, 1, "B", "after_snap", 20, 12, 0.5, 2.5),
        make_row(1, 1, "B", "before_pass", 15, 8, 1.2, 3.2),
        make_row(2, 2, "A", "after_snap", 110, 85, 0.5, 2.5),
        make_row(2, 2, "A", "before_pass", 115, 80, 1.2, 3.2),
        make_row(2, 2, "B", "after_snap", 25, 17, 0.5, 2.5),
        make_row(2, 2, "B", "before_pass", 18, 12, 1.2, 3.2),
    ]
    assert actual_rows == expected
