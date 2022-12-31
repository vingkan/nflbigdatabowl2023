import pandas as pd

from src.pipeline.tasks.dataframes import limit_by_child_keys, limit_by_keys


def test_limit_by_keys():
    df = pd.DataFrame(
        [
            # Keep both these rows because their key is included.
            {"a": 1, "b": 1, "c": 1},
            {"a": 1, "b": 1, "c": 2},
            # Keep both these rows because their key is included.
            {"a": 1, "b": 2, "c": 1},
            {"a": 1, "b": 2, "c": 2},
            # Discard these rows because we have reached the limit.
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


def test_limit_by_child_keys():
    df = pd.DataFrame(
        [
            # Keep the first two rows for this parent key.
            {"x": 1, "y": 1, "z": 1},
            {"x": 1, "y": 2, "z": 2},
            {"x": 1, "y": 3, "z": 3},
            # Keep the first two rows if their child key was included.
            {"x": 1, "y": 1, "z": 4},
            {"x": 1, "y": 2, "z": 5},
            {"x": 1, "y": 3, "z": 6},
            # Keep the first two rows for this parent key, sort by child key.
            {"x": 2, "y": 1, "z": 7},
            {"x": 2, "y": 3, "z": 9},
            {"x": 2, "y": 2, "z": 8},
        ]
    )
    actual = limit_by_child_keys(df, parent_keys=["x"], child_keys=["y"], n=2)
    expected = [
        {"x": 1, "y": 1, "z": 1},
        {"x": 1, "y": 1, "z": 4},
        {"x": 1, "y": 2, "z": 2},
        {"x": 1, "y": 2, "z": 5},
        {"x": 2, "y": 1, "z": 7},
        {"x": 2, "y": 2, "z": 8},
    ]
    assert actual.to_dict(orient="records") == expected
