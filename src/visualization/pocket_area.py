from typing import Dict, Optional

import dacite
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Patch, Polygon
from matplotlib.ticker import MultipleLocator

from src.metrics.pocket_area.base import InvalidPocketError, PocketArea

POCKET_KWARGS = dict(
    color="#b0e3ff",
    alpha=0.5,
)

PocketAreaNestedMap = Dict[int, Dict[str, PocketArea]]


def get_pocket_area_nested_map(df_areas: pd.DataFrame) -> PocketAreaNestedMap:
    output: PocketAreaNestedMap = {}
    for i, row in df_areas.iterrows():
        # Retrieve keys from DataFrame.
        frame_id = row["frameId"]
        method = row["method"]
        pocket_dict = row["pocket"]

        # Parse pocket area dataclass.
        # The dataclass does not allow a None for area, but we cannot parse a
        # np.nan from a string, so if the area is None, set it to np.nan.
        if pocket_dict["area"] is None:
            pocket_dict["area"] = np.nan
        pocket = dacite.from_dict(PocketArea, pocket_dict)

        # Update nested map.
        if frame_id not in output:
            output[frame_id] = {}
        output[frame_id][method] = pocket

    return output


def get_pocket_patch_for_vertices(pocket: PocketArea) -> Patch:
    """Gets the graphic patch for a pocket defined by a list of vertices."""
    vertices = pocket.metadata.vertices
    if vertices is None:
        raise InvalidPocketError("No verticies in pocket metadata.")

    return Polygon(vertices, **POCKET_KWARGS, fill=True)


def get_pocket_patch_for_circle(pocket: PocketArea) -> Patch:
    """Gets the graphic patch for a pocket defined as a circle."""
    center = pocket.metadata.center
    radius = pocket.metadata.radius
    if center is None or radius is None:
        raise InvalidPocketError("No center or radius in pocket metadata.")

    return Circle(center, radius, **POCKET_KWARGS)


def get_pocket_patch(pocket: PocketArea) -> Optional[Patch]:
    """Gets the graphic patch for a pocket, if possible."""
    vertices = pocket.metadata.vertices
    center = pocket.metadata.center
    radius = pocket.metadata.radius

    is_vertices_based = vertices is not None
    is_circular = center is not None and radius is not None

    if is_vertices_based:
        return get_pocket_patch_for_vertices(pocket)
    elif is_circular:
        return get_pocket_patch_for_circle(pocket)
    return None
