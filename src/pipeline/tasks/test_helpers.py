from typing import Any, Callable, Dict, List

RowColumns = List[str]
RowValues = List[Any]
RowDict = Dict[str, Any]


def row_creator(columns: RowColumns) -> Callable[[RowValues], RowDict]:
    """Returns a test helper function to create a row."""

    def create_row(*values: RowValues) -> RowDict:
        """Inner function to zip columns and values into a row dictionary."""
        return {col: val for col, val in zip(columns, values)}

    return create_row
