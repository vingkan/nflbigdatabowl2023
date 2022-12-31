from pathlib import Path
from typing import List, Optional

import pandas as pd


def read_csv(infile: str) -> pd.DataFrame:
    """Reads a DataFrame from a CSV file path."""
    return pd.read_csv(infile)


def write_csv(df: pd.DataFrame, outfile: str):
    """
    Writes a DataFrame to a CSV file path and creates parent directories if
    they do not exist.
    """
    outpath = Path(outfile).parent
    outpath.mkdir(parents=True, exist_ok=True)
    df.to_csv(outfile, index=False)


def union_dataframes(df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """Unions a list of DataFrames, assuming they have the same columns."""
    return pd.concat(df_list)


def limit_by_keys(
    df: pd.DataFrame, keys: List[str], n=Optional[int]
) -> pd.DataFrame:
    """
    Limits a DataFrame to the rows for the first n combinations of the given
    keys, using the default sort. If no limit is requested, returns the input
    DataFrame.
    """
    if n is None:
        return df

    df_unique = df[keys].drop_duplicates()
    df_limited = df_unique.sort_values(keys).head(n)
    # Left join to reduce the original DataFrame to only the limited rows, if
    # right side contains multiple rows for the given key, the join will explode
    # resulting in retaining those rows.
    df_output = df_limited.merge(df, on=keys, how="left")
    return df_output


def limit_by_child_keys(
    df: pd.DataFrame,
    parent_keys: List[str],
    child_keys: List[str],
    n=Optional[int],
) -> pd.DataFrame:
    """
    Limits a DataFrame so that each subgroup of the parent keys only has up to n
    combinations of the child keys, using the default sort. If no limit is
    requested, returns the input DataFrame.
    """
    if n is None:
        return df

    full_keys = parent_keys + child_keys
    df_unique = df[full_keys].drop_duplicates()
    # Only need to sort on child keys because limit will be taken within each
    # parent group, so parent keys do not affect the limit.
    df_sorted = df_unique.sort_values(full_keys)
    # Take the first n rows in each group.
    df_limited = df_sorted.groupby(parent_keys).head(n).reset_index(drop=True)
    # Left join to reduce the original DataFrame to only the limited rows, if
    # right side contains multiple rows for the given parent and child key, the
    # join will explode resulting in retaining those rows.
    df_output = df_limited.merge(df, on=full_keys, how="left")
    return df_output
