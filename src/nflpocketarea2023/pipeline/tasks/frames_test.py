import pandas as pd

from nflpocketarea2023.pipeline.tasks.frames import (
    transform_to_frames,
    transform_to_records_per_frame,
)


def test_transform_to_frames():
    df_tracking = pd.DataFrame(
        [
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 1,
                "nflId": 1,
                "x": 1,
                "y": 1,
            },
        ]
    )
    df_pff = pd.DataFrame(
        [
            {"gameId": 1, "playId": 1, "nflId": 1, "pff_role": "Pass"},
        ]
    )
    actual = transform_to_frames(df_tracking, df_pff)
    expected = [
        {
            "gameId": 1,
            "playId": 1,
            "frameId": 1,
            "nflId": 1,
            "x": 1,
            "y": 1,
            "role": "passer",
        },
    ]
    assert actual.to_dict(orient="records") == expected


def test_transform_to_records_per_frame():
    df_frames = pd.DataFrame(
        [
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 1,
                "x": 1,
                "y": 1,
                "role": "passer",
            },
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 1,
                "x": 2,
                "y": 2,
                "role": "blocker",
            },
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 1,
                "x": 3,
                "y": 3,
                "role": "rusher",
            },
        ]
    )
    actual = transform_to_records_per_frame(df_frames)
    expected = [
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
    assert actual.to_dict(orient="records") == expected
