import pytest

from src.metrics.pocket_area.rushers_pocket_area import rushers_pocket_area


def test_rushers_pocket_area():

    frame = [
        {"role": "passer", "x": 0, "y": 0},
        {"role": "rusher", "x": 1, "y": 1},
        {"role": "rusher", "x": 1, "y": -1},
        {"role": "rusher", "x": -1, "y": -1},
        {"role": "rusher", "x": -1, "y": 1},
        {"role": "rusher", "x": 0, "y": 2},
        {"role": "rusher", "x": 0.5, "y": 0.5},
        {"role": "blocker", "x": 2, "y": 1},
        {"role": "blocker", "x": 2, "y": -1},
        {"role": "blocker", "x": -2, "y": -1},
        {"role": "blocker", "x": -2, "y": 1},
        {"role": "blocker", "x": 0, "y": 3},
    ]

    pocket_area = rushers_pocket_area(frame)
    assert pocket_area.area == pytest.approx(5)
    assert pocket_area.metadata.vertices == [
        (-1, -1),
        (1, -1),
        (1, 1),
        (0, 2),
        (-1, 1),
    ]
