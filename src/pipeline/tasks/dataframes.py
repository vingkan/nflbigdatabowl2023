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
    df: pd.DataFrame, keys: List[str], n=Optional[float]
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
    df_output = df_limited.merge(df, on=keys, how="left")
    return df_output
