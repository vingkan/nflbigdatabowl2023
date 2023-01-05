import pytest

from src.metrics.pocket_area.adaptive_pocket_area import (
    calculate_adaptive_pocket_area,
)
from src.metrics.pocket_area.helpers import InvalidPocketError


def test_one_rusher_valid_to_make_pocket():
    frame = [
        {"role": "passer", "x": 0, "y": 5},
        {"role": "blocker", "x": 0, "y": 0},
        {"role": "blocker", "x": 1, "y": 2},
        {"role": "blocker", "x": 5, "y": 0},
        {"role": "blocker", "x": 5, "y": 5},
        {"role": "blocker", "x": 0, "y": -2},
        {"role": "rusher", "x": 1, "y": 6},
        {"role": "rusher", "x": 5, "y": 5},
    ]
    actual = calculate_adaptive_pocket_area(frame)

    assert actual.area == pytest.approx(2.094395102393196)
    assert actual.metadata.edge == (1, 6)


def test_multiple_rushers_valid_to_make_pocket():
    frame = [
        {"role": "passer", "x": 0, "y": 5},
        {"role": "blocker", "x": 0, "y": 0},
        {"role": "blocker", "x": 1, "y": 2},
        {"role": "blocker", "x": 5, "y": 0},
        {"role": "blocker", "x": 5, "y": 5},
        {"role": "blocker", "x": 0, "y": -2},
        {"role": "rusher", "x": 1, "y": 6},
        {"role": "rusher", "x": 5, "y": 5},
        {"role": "rusher", "x": 1, "y": 4},
        {"role": "rusher", "x": 2, "y": 6},
    ]
    actual = calculate_adaptive_pocket_area(frame)

    assert actual.area == pytest.approx(2.0)
    assert actual.metadata.vertices == [
        (0.0, 5.0),
        (1.0, 4.0),
        (2.0, 6.0),
        (1.0, 6.0),
    ]
