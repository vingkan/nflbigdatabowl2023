import pandas as pd

from src.pipeline.tasks.dataframes import limit_by_keys


def test_limit_by_keys():
    df = pd.DataFrame(
        [
            {"a": 1, "b": 1, "c": 1},
            {"a": 1, "b": 1, "c": 2},
            {"a": 1, "b": 2, "c": 1},
            {"a": 1, "b": 2, "c": 2},
            {"a": 2, "b": 1, "c": 1},
            {"a": 2, "b": 1, "c": 2},
        ]
    )
    actual = limit_by_keys(df, keys=["a", "b"], n=2)
    expected = [
        {"a": 1, "b": 1, "c": 1},
        {"a": 1, "b": 1, "c": 2},
        {"a": 1, "b": 2, "c": 1},
        {"a": 1, "b": 2, "c": 2},
    ]
    assert actual.to_dict(orient="records") == expected
