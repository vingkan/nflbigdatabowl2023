import pandas as pd
import pytest

from nflpocketarea2023.pipeline.tasks.play_metrics import (
    calculate_average_pocket_area_loss_per_second,
    get_play_pocket_metrics,
)
from nflpocketarea2023.pipeline.tasks.test_helpers import row_creator


def test_get_play_pocket_metrics():
    # Helper function to create input rows.
    input_columns = [
        "gameId",
        "playId",
        "method",
        "window_type",
        "frameId",
        "area",
    ]
    input_row = row_creator(input_columns)

    # Create input data.
    df = pd.DataFrame(
        [
            # Frames inside window, but not outside window.
            input_row(1, 1, "A", "after_snap", 5, 100),
            input_row(1, 1, "A", "after_snap", 6, 120),
            input_row(1, 1, "A", "after_snap", 25, 80),
            # Multiple pocket area methods.
            input_row(1, 1, "B", "after_snap", 5, 20),
            input_row(1, 1, "B", "after_snap", 6, 30),
            input_row(1, 1, "B", "after_snap", 25, 12),
            # Multiple window types.
            input_row(1, 1, "A", "before_pass", 12, 110),
            input_row(1, 1, "A", "before_pass", 32, 75),
            input_row(1, 1, "B", "before_pass", 12, 15),
            input_row(1, 1, "B", "before_pass", 32, 8),
            # Multiple plays.
            input_row(2, 2, "A", "after_snap", 5, 110),
            input_row(2, 2, "A", "after_snap", 6, 130),
            input_row(2, 2, "A", "after_snap", 25, 85),
            input_row(2, 2, "A", "after_snap", 6, 25),
            input_row(2, 2, "B", "after_snap", 5, 25),
            input_row(2, 2, "B", "after_snap", 25, 17),
            input_row(2, 2, "A", "before_pass", 12, 115),
            input_row(2, 2, "A", "before_pass", 32, 80),
            input_row(2, 2, "B", "before_pass", 12, 18),
            input_row(2, 2, "B", "before_pass", 32, 12),
        ]
    )

    # Run actual transformation.
    actual = get_play_pocket_metrics(df)

    # Sort actual rows and convert to dictionaries.
    sort_columns = ["gameId", "playId", "method", "window_type"]
    actual_rows = actual.sort_values(sort_columns).to_dict(orient="records")

    # Helper function to create output rows.
    output_columns = [
        "gameId",
        "playId",
        "method",
        "window_type",
        "area_start",
        "area_end",
        "time_start",
        "time_end",
        "median_area",
        "average_area",
    ]
    output_row = row_creator(output_columns)

    # Compare to expected rows.
    a_20_6 = pytest.approx(20.666666)
    expected = [
        output_row(1, 1, "A", "after_snap", 100, 80, 0.5, 2.5, 100.0, 100.0),
        output_row(1, 1, "A", "before_pass", 110, 75, 1.2, 3.2, 92.5, 92.5),
        output_row(1, 1, "B", "after_snap", 20, 12, 0.5, 2.5, 20.0, a_20_6),
        output_row(1, 1, "B", "before_pass", 15, 8, 1.2, 3.2, 11.5, 11.5),
        output_row(2, 2, "A", "after_snap", 110, 85, 0.5, 2.5, 97.5, 87.5),
        output_row(2, 2, "A", "before_pass", 115, 80, 1.2, 3.2, 97.5, 97.5),
        output_row(2, 2, "B", "after_snap", 25, 17, 0.5, 2.5, 21.0, 21.0),
        output_row(2, 2, "B", "before_pass", 18, 12, 1.2, 3.2, 15.0, 15.0),
    ]
    assert actual_rows == expected


def test_calculate_average_pocket_area_loss_per_second():
    # Helper function to create input rows.
    input_columns = [
        "gameId",
        "playId",
        "method",
        "window_type",
        "area_start",
        "area_end",
        "time_start",
        "time_end",
    ]
    input_row = row_creator(input_columns)

    # Create input rows.
    df = pd.DataFrame(
        [
            input_row(1, 1, "A", "after_snap", 100, 80, 0.5, 2.5),
            input_row(1, 1, "A", "before_pass", 110, 75, 1.2, 3.2),
            input_row(1, 1, "B", "after_snap", 20, 12, 0.5, 2.5),
            input_row(1, 1, "B", "before_pass", 15, 8, 1.2, 3.2),
            input_row(2, 2, "B", "after_snap", 25, 17, 0.5, 2.5),
        ]
    )

    # Run actual transformation.
    actual = calculate_average_pocket_area_loss_per_second(df)

    # Helper function to create output rows.
    output_columns = [
        "gameId",
        "playId",
        "method",
        "window_type",
        "average_pocket_area_loss_per_second",
    ]
    output_row = row_creator(output_columns)

    # Retrict actual rows to output columns and convert to dictionaries.
    actual_rows = actual[output_columns].to_dict(orient="records")

    # Compare to expected rows.
    expected = [
        output_row(1, 1, "A", "after_snap", -10.0),
        output_row(1, 1, "A", "before_pass", -17.5),
        output_row(1, 1, "B", "after_snap", -4.0),
        output_row(1, 1, "B", "before_pass", -3.5),
        output_row(2, 2, "B", "after_snap", -4.0),
    ]
    assert actual_rows == expected
