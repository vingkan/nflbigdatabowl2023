from typing import Dict, Optional

import dacite
import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle, Patch, Polygon
from matplotlib.ticker import MultipleLocator

from src.metrics.pocket_area.base import InvalidPocketError, PocketArea

POCKET_COLOR = "#b0e3ff"

PocketAreaNestedMap = Dict[int, Dict[str, PocketArea]]


def get_pocket_area_nested_map(df_areas: pd.DataFrame) -> PocketAreaNestedMap:
    output: PocketAreaNestedMap = {}
    for i, row in df_areas.iterrows():
        # Retrieve keys from DataFrame.
        frame_id = row["frameId"]
        method = row["method"]
        pocket_dict = row["pocket"]

        # Parse pocket area dataclass.
        pocket = dacite.from_dict(PocketArea, pocket_dict)

        # Update nested map.
        if frame_id not in output:
            output[frame_id] = {}
        output[frame_id][method] = pocket

    return output


def get_pocket_patch_from_vertices(pocket: PocketArea) -> Patch:
    """Gets the graphic patch for a pocket from a list of vertices."""
    if not pocket.metadata or not pocket.metadata.vertices:
        raise InvalidPocketError("No verticies in pocket metadata.")

    vertices = pocket.metadata.vertices
    return Polygon(vertices, color=POCKET_COLOR, fill=True)


def get_pocket_patch(pocket: PocketArea) -> Optional[Patch]:
    """Gets the graphic patch for a pocket, if possible."""
    if not pocket.metadata:
        return None

    if pocket.metadata.vertices:
        return get_pocket_patch_from_vertices(pocket)

    # TODO(vinesh): Add support for pockets with radius and center.

    return None
