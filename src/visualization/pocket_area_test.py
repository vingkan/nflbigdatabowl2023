import pandas as pd
from matplotlib.patches import Circle, Polygon

from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata
from src.visualization.pocket_area import (
    get_pocket_area_nested_map,
    get_pocket_patch,
)


def test_get_pocket_area_nested_map():
    df = pd.DataFrame(
        [
            {
                "frameId": 1,
                "method": "a",
                "pocket": {"area": 1, "metadata": {}},
            },
            {
                "frameId": 1,
                "method": "b",
                "pocket": {
                    "area": 2,
                    "metadata": {"center": (1, 1), "radius": 1},
                },
            },
            {
                "frameId": 2,
                "method": "a",
                "pocket": {"area": 3, "metadata": {}},
            },
            {
                "frameId": 2,
                "method": "b",
                "pocket": {
                    "area": 4,
                    "metadata": {"vertices": [(1, 1), (0, 0), (2, 2)]},
                },
            },
        ]
    )
    actual = get_pocket_area_nested_map(df)
    expected = {
        1: {
            "a": PocketArea(area=1),
            "b": PocketArea(
                area=2, metadata=PocketAreaMetadata(center=(1, 1), radius=1)
            ),
        },
        2: {
            "a": PocketArea(area=3),
            "b": PocketArea(
                area=4,
                metadata=PocketAreaMetadata(vertices=[(1, 1), (0, 0), (2, 2)]),
            ),
        },
    }
    assert actual == expected


def test_get_pocket_no_metadata():
    pocket = PocketArea(area=7)
    assert get_pocket_patch(pocket) is None


def test_get_pocket_patch_vertices():
    pocket = PocketArea(
        area=6, metadata=PocketAreaMetadata(vertices=[(0, 0), (1, 1), (2, 2)])
    )
    actual = get_pocket_patch(pocket)
    expected = Polygon([(0, 0), (1, 1), (2, 2)])
    # Patch objects do not support equality, so we test the available properties
    assert type(actual) == type(expected)
    assert (actual.xy == expected.xy).all()


def test_get_pocket_patch_circle():
    pocket = PocketArea(
        area=9, metadata=PocketAreaMetadata(center=(1, 1), radius=7)
    )
    actual = get_pocket_patch(pocket)
    expected = Circle((1, 1), 7)
    # Patch objects do not support equality, so we test the available properties
    assert type(actual) == type(expected)
    assert actual.radius == expected.radius
