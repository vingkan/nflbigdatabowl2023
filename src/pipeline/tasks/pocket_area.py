from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.metrics.pocket_area.base import PocketAreaFunction
from src.pipeline.tasks.frames import FRAME_PRIMARY_KEY


def calculate_area_safely(
    calculate_fn: PocketAreaFunction,
) -> PocketAreaFunction:
    """
    Wraps a pocket area calculation function to return a null value if the
    calculation function raises an exception.
    """

    def calculate(records: List[Dict]) -> float:
        try:
            return calculate_fn(records)
        except Exception:
            return np.nan

    return calculate


def calculate_pocket_area(
    df_frame_records: pd.DataFrame, method: Tuple[str, PocketAreaFunction]
) -> pd.DataFrame:
    """Applies a pocket area calculation method to each frame in the input."""
    method_name, calculate_fn = method
    calculate_area: PocketAreaFunction = calculate_area_safely(calculate_fn)
    ser_area = df_frame_records["records"].apply(calculate_area)
    ser_method = [method_name] * len(ser_area)
    df_area = pd.DataFrame({"method": ser_method, "area": ser_area})
    df_keys = df_frame_records[FRAME_PRIMARY_KEY]
    df_output = pd.concat([df_keys, df_area], axis=1)
    return df_output
