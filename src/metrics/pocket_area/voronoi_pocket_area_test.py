import pytest

from src.metrics.pocket_area.voronoi_pocket_area import voronoi_pocket_area


def test_voronoi_pocket_area():

    frame = [
        {"role": "passer", "x": 5, "y": 5},
        {"role": "rusher", "x": 1, "y": 9},
        {"role": "rusher", "x": 9, "y": 9},
        {"role": "blocker", "x": 1, "y": 1},
        {"role": "blocker", "x": 9, "y": 1},
    ]

    pocket_area = voronoi_pocket_area(frame)
    assert pocket_area.area == pytest.approx(23)
    assert pocket_area.metadata.vertices == [
        (8, 4),
        (9, 5),
        (5, 9),
        (1, 5),
        (2, 4),
    ]
