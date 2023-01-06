import pytest

from src.metrics.pocket_area.voronoi_rushers_only import voronoi_rushers_only


def test_voronoi_rushers_only():

    frame = [
        {"role": "passer", "x": 25, "y": -5},
        {"role": "rusher", "x": 23, "y": -9},
        {"role": "rusher", "x": 27, "y": -9},
        {"role": "rusher", "x": 21.8, "y": 1.4},
        {"role": "rusher", "x": 28.2, "y": 1.4},
        {"role": "blocker", "x": 21, "y": -9},
        {"role": "blocker", "x": 29, "y": -9},
        {"role": "blocker", "x": 19.8, "y": 1.4},
        {"role": "blocker", "x": 30.2, "y": 1.4},
    ]

    pocket_area = voronoi_rushers_only(frame)
    assert pocket_area.area == pytest.approx(31)
    assert pocket_area.metadata.vertices == [
        (22.0, -6.0),
        (28.0, -6.0),
        (30.0, -5.0),
        (30.0, -3.4999999999999996),
        (28.0, -2.5),
        (22.0, -2.5),
        (20.0, -3.4999999999999996),
        (20.0, -5.0),
    ]
