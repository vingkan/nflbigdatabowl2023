from nflpocketarea2023.pipeline.tasks.test_helpers import row_creator


def test_row_creator():
    create_row = row_creator(["a", "b", "c"])
    actual = create_row("A", 2, None)
    expected = {"a": "A", "b": 2, "c": None}
    assert actual == expected
