import numpy as np
import pytest

from src.metrics.pocket_area.base import (
    InvalidPocketError,
    PocketArea,
    PocketAreaMetadata,
)
from src.metrics.pocket_area.helpers import (
    convert_pff_role_to_pocket_role,
    get_distance,
    pocket_from_json,
    pocket_to_json,
    split_records_by_role,
)


def test_split_records_by_role():
    frame = [
        {"role": "blocker", "x": 1, "y": 0},
        # If the frame includes multiple passers, the first will be returned
        {"role": "passer", "x": 2, "y": 0},
        {"role": "passer", "x": 3, "y": 0},
        {"role": "rusher", "x": 4, "y": 0},
        {"role": "blocker", "x": 5, "y": 0},
        {"role": "rusher", "x": 6, "y": 0},
    ]
    actual = split_records_by_role(frame)

    expected_passer = {"role": "passer", "x": 2, "y": 0}
    expected_blockers = [
        {"role": "blocker", "x": 1, "y": 0},
        {"role": "blocker", "x": 5, "y": 0},
    ]
    expected_rushers = [
        {"role": "rusher", "x": 4, "y": 0},
        {"role": "rusher", "x": 6, "y": 0},
    ]
    expected = (expected_passer, expected_blockers, expected_rushers)
    assert actual == expected


def test_split_records_by_role_no_passer_found():
    expected = "No passer in frame."
    with pytest.raises(InvalidPocketError, match=expected):
        split_records_by_role(frame=[])


def test_get_distance_one_dimension():
    actual = get_distance(a={"x": 1, "y": 0}, b={"x": 2, "y": 0})
    assert actual == pytest.approx(1.0)


def test_get_distance_two_dimensions():
    actual = get_distance(a={"x": 1, "y": 1}, b={"x": 2, "y": 2})
    assert actual == pytest.approx(1.414213)


def test_get_distance_missing_b_x_coordinate():
    expected = "Coordinates must not be null."
    with pytest.raises(ValueError, match=expected):
        get_distance(a={"x": 1, "y": 1}, b={"y": 2})


def test_convert_pff_role_to_pocket_role():
    assert convert_pff_role_to_pocket_role("Pass Block") == "blocker"
    assert convert_pff_role_to_pocket_role("Football") == "unknown"
    assert convert_pff_role_to_pocket_role("Something Else") == "unknown"


def test_pocket_from_json():
    data = {"area": 7.12, "metadata": {"vertices": [(0, 1), (2, 3)]}}
    actual = pocket_from_json(data)
    expected = PocketArea(
        area=7.12,
        metadata=PocketAreaMetadata(vertices=[(0, 1), (2, 3)]),
    )
    assert actual == expected


def test_pocket_from_json_null_area():
    data = {
        "area": None,
        "metadata": {"radius": 12, "center": (4, 5)},
    }
    actual = pocket_from_json(data)
    expected = PocketArea(
        area=np.nan, metadata=PocketAreaMetadata(radius=12, center=(4, 5))
    )
    assert actual == expected


def test_pocket_from_json_no_metadata():
    data = {"area": 42}
    actual = pocket_from_json(data)
    expected = PocketArea(area=42)
    assert actual == expected


def test_pocket_to_json():
    pocket = PocketArea(
        area=7.12,
        metadata=PocketAreaMetadata(vertices=[(0, 1), (2, 3)]),
    )
    actual = pocket_to_json(pocket)
    expected = {"area": 7.12, "metadata": {"vertices": [(0, 1), (2, 3)]}}
    assert actual == expected


def test_pocket_to_json_null_area():
    pocket = PocketArea(
        area=np.nan,
        metadata=PocketAreaMetadata(radius=12, center=(4, 5)),
    )
    actual = pocket_to_json(pocket)
    expected = {
        "area": None,
        "metadata": {"radius": 12, "center": (4, 5)},
    }
    assert actual == expected


def test_pocket_to_json_no_metadata():
    pocket = PocketArea(area=42)
    actual = pocket_to_json(pocket)
    expected = {"area": 42}
    assert actual == expected
