import pytest

from src.metrics.pocket_area.voronoi_pocket_area import voronoi_pocket_area


def test_voronoi_pocket_area():

    frame = [
        {"role": "passer", "x": 15, "y": 5},
        {"role": "rusher", "x": 11, "y": 9},
        {"role": "rusher", "x": 19, "y": 9},
        {"role": "blocker", "x": 11, "y": 1},
        {"role": "blocker", "x": 19, "y": 1},
    ]

    pocket_area = voronoi_pocket_area(frame)
    assert pocket_area.area == pytest.approx(23)
    assert pocket_area.metadata.vertices == [
        (12, 4),
        (11, 5),
        (15, 9),
        (19, 5),
        (18, 4),
    ]
