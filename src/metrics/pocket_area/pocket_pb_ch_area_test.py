import pytest

from src.metrics.pocket_area.helpers import InvalidPocketError
from src.metrics.pocket_area.pocket_pb_ch_area import (
    get_passBlocker_convexHull_area,
)


def test_get_get_passBlocker_convexHull_area():
    frame = [
        {"role": "passer", "x": 0, "y": 5},
        {"role": "blocker", "x": 0, "y": 0},
        {"role": "blocker", "x": 1, "y": 2},
        {"role": "blocker", "x": 5, "y": 0},
        {"role": "blocker", "x": 5, "y": 5},
    ]
    actual = get_passBlocker_convexHull_area(frame)
    assert actual.area == pytest.approx(25)
    assert actual.metadata.vertices == [(0, 0), (5, 0), (5, 5), (0, 5)]
