from typing import Any, Callable, Dict, List

RowColumns = List[str]
RowValues = List[Any]
RowDict = Dict[str, Any]


def row_creator(expected_columns: RowColumns) -> Callable[[RowValues], RowDict]:
    """Returns a test helper function to create an expected output row."""

    def create_row(*expected_values: RowValues) -> RowDict:
        """Inner function to zip values and headers into a row dictionary."""
        return {col: val for col, val in zip(expected_columns, expected_values)}

    return create_row
