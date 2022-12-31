import pandas as pd
import pytest

from src.pipeline.tasks.tracking import (
    align_tracking_data,
    rotate_tracking_data,
)


def approx_one_decimal(expected: float):
    """
    Test helper function to check if another float is approximately equal to the
    given expected float, at a tolerance of +/- 0.1.
    """
    return pytest.approx(expected, abs=1e-1)


def test_align_tracking_data():
    df_tracking = pd.DataFrame(
        [
            {"playDirection": "right", "x": 30, "y": 50, "o": 90, "dir": 0},
            # After alignment, the coordinates should be:
            # x: 80 yards from left endline -> 40 yards from left endline
            # y: 10 yards from bottom sideline -> 43.3 yards from bottom sideline
            {"playDirection": "left", "x": 80, "y": 10, "o": 270, "dir": 180},
        ]
    )
    actual = align_tracking_data(df_tracking)
    expected = [
        {"playDirection": "right", "x": 30, "y": 50, "o": 90, "dir": 0},
        {
            "playDirection": "right",
            "x": 40,
            "y": approx_one_decimal(43.3),
            "o": 90,
            "dir": 0,
        },
    ]
    assert actual.to_dict(orient="records") == expected


def test_rotate_tracking_data():
    df_tracking = pd.DataFrame(
        [
            {"playDirection": "right", "x": 30, "y": 50, "o": 90, "dir": 0},
            {"playDirection": "right", "x": 30, "y": 3, "o": 180, "dir": 315},
        ]
    )
    actual = rotate_tracking_data(df_tracking)
    expected = [
        {
            "playDirection": "right",
            "x": approx_one_decimal(3.3),
            "y": 30,
            "o": 0,
            "dir": 270,
        },
        {
            "playDirection": "right",
            "x": approx_one_decimal(50.3),
            "y": 30,
            "o": 90,
            "dir": 225,
        },
    ]
    assert actual.to_dict(orient="records") == expected
