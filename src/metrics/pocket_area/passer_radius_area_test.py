import pytest

from src.metrics.pocket_area.helpers import InvalidPocketError
from src.metrics.pocket_area.passer_radius_area import get_passer_radius_area


def test_get_passer_radius_area():
    frame = [
        {"role": "passer", "x": 0, "y": 0},
        {"role": "blocker", "x": 0, "y": -2},
        {"role": "rusher", "x": 0, "y": 2},
        {"role": "rusher", "x": 0, "y": 4},
    ]
    actual = get_passer_radius_area(frame)
    # Closest rusher is 2 units away, so area is: 3.14 * (2^2) ~= 12.5
    assert actual.area == pytest.approx(12.566370)
    assert actual.metadata.radius == 2
    assert actual.metadata.center == (0, 0)


def test_get_passer_radius_area_no_rushers():
    frame = [{"role": "passer", "x": 0, "y": 0}]

    expected = "No rushers in frame."
    with pytest.raises(InvalidPocketError, match=expected):
        get_passer_radius_area(frame)
