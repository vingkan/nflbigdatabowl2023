import pandas as pd

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
