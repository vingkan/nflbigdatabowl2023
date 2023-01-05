import re
from typing import Dict, List

import numpy as np
import pandas as pd
import pytest

from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata
from src.pipeline.tasks.pocket_area import (
    calculate_pocket_area,
    calculate_pocket_safely,
)


def test_calculate_pocket_area():
    df = pd.DataFrame(
        [
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 1,
                "records": [
                    {"x": 1, "y": 1, "role": "passer"},
                    {"x": 2, "y": 2, "role": "blocker"},
                    {"x": 3, "y": 3, "role": "rusher"},
                ],
            }
        ]
    )

    def calculate_area_always_seven(records: List[Dict]) -> PocketArea:
        return PocketArea(area=7)

    method = ("always_seven", calculate_area_always_seven)
    actual = calculate_pocket_area(df, method)
    expected = [
        {
            "gameId": 1,
            "playId": 1,
            "frameId": 1,
            "method": "always_seven",
            "pocket": {
                "area": 7,
                "metadata": {
                    "vertices": None,
                    "radius": None,
                    "center": None,
                },
            },
            "area": 7,
        },
    ]
    assert actual.to_dict(orient="records") == expected


def test_calculate_pocket_safely():
    def calculate_area_always_seven(records: List[Dict]) -> PocketArea:
        return PocketArea(area=7)

    actual_fn = calculate_pocket_safely(calculate_area_always_seven)

    df = pd.DataFrame()
    actual = actual_fn(df)
    expected = {
        "area": 7,
        "metadata": {"vertices": None, "radius": None, "center": None},
    }
    assert actual == expected


def test_calculate_pocket_safely_with_exception():
    def calculate_area_raises_exception(records: List[Dict]) -> PocketArea:
        raise Exception("This function does not work.")

    actual_fn = calculate_pocket_safely(calculate_area_raises_exception)

    df = pd.DataFrame()
    actual = actual_fn(df)
    expected = {
        "area": None,
        "metadata": {"vertices": None, "radius": None, "center": None},
    }
    assert actual == expected


def test_calculate_pocket_safely_with_invalid_function():
    def calculate_area_returns_wrong_type(records: List[Dict]) -> float:
        return 6

    actual_fn = calculate_pocket_safely(calculate_area_returns_wrong_type)

    expected = re.escape(
        "Function calculate_area_returns_wrong_type() returned int instead of PocketArea."
    )
    with pytest.raises(TypeError, match=expected):
        df = pd.DataFrame()
        actual_fn(df)
