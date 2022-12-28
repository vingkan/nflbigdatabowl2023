from typing import Dict, List

import pandas as pd

from src.pipeline.tasks.pocket_area import calculate_pocket_area


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

    def calculate_area(records: List[Dict]) -> float:
        return 7

    method = ("always_seven", calculate_area)
    actual = calculate_pocket_area(df, method)
    expected = [
        {
            "gameId": 1,
            "playId": 1,
            "frameId": 1,
            "method": "always_seven",
            "area": 7,
        },
    ]
    assert actual.to_dict(orient="records") == expected
