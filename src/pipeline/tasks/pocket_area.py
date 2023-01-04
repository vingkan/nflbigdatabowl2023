import dataclasses
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.metrics.pocket_area.base import PocketArea, PocketAreaFunction
from src.pipeline.tasks.frames import FRAME_PRIMARY_KEY


def calculate_pocket_safely(
    calculate_fn: PocketAreaFunction,
) -> Callable[[List[Dict]], Dict]:
    """
    Wraps a pocket area calculation function to return a null value if the
    calculation function raises an exception. Returns the pocket area and any
    metadata as a dictionary.
    """
    function_name = f"{calculate_fn.__name__}()"

    def calculate(records: List[Dict]) -> Dict:
        # If pocket area calculation fails, return a pocket with null area.
        try:
            pocket_area = calculate_fn(records)
        except Exception as ex:
            print(f"Exception in {function_name}: {ex}")
            pocket_area = PocketArea(area=np.nan)

        if not isinstance(pocket_area, PocketArea):
            actual_type = type(pocket_area).__name__
            message = f"Function {function_name} returned {actual_type} instead of PocketArea."
            raise TypeError(message)

        # Convert the pocket area dataclass to a dictionary.
        # The dataclass does not allow a None for area, but we cannot parse a
        # np.nan from a string, so if the area is np.nan, set it to None.
        pocket_dict = dataclasses.asdict(pocket_area)
        if np.isnan(pocket_dict["area"]):
            pocket_dict["area"] = None
        return pocket_dict

    return calculate


def get_area_from_dict(pocket: Dict) -> float:
    """
    Retrieves the area value from the pocket dictionary, with a null value if
    no area is found.
    """
    return pocket.get("area", np.nan)


def calculate_pocket_area(
    df_frame_records: pd.DataFrame, method: Tuple[str, PocketAreaFunction]
) -> pd.DataFrame:
    """Applies a pocket area calculation method to each frame in the input."""
    method_name, calculate_fn = method
    calculate_pocket = calculate_pocket_safely(calculate_fn)
    ser_pocket = df_frame_records["records"].apply(calculate_pocket)
    ser_method = [method_name] * len(ser_pocket)
    df_area = pd.DataFrame({"method": ser_method, "pocket": ser_pocket})
    df_area["area"] = df_area["pocket"].apply(get_area_from_dict)
    df_keys = df_frame_records[FRAME_PRIMARY_KEY]
    df_output = pd.concat([df_keys, df_area], axis=1)
    return df_output
