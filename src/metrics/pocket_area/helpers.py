import dataclasses
import math
from typing import Dict, List, Tuple

import numpy as np
from shapely import Polygon

from src.metrics.pocket_area.base import (
    PFF_ROLE_TO_POCKET_ROLE,
    InvalidPocketError,
    PFFRole,
    PocketArea,
    PocketAreaMetadata,
    PocketRole,
)

# Tuple of form (passer, blockers, rushers)
PlayerRecordsByRole = Tuple[Dict, List[Dict], List[Dict]]


def split_records_by_role(frame: List[Dict]) -> PlayerRecordsByRole:
    """Splits the players in a frame by role and returns them."""
    passer: Dict = {}
    blockers: List[Dict] = []
    rushers: List[Dict] = []

    for player in frame:
        raw_role = player.get("role")
        player_role = PocketRole(raw_role)
        # If multiple passers, only return the first passer.
        if player_role == PocketRole.PASSER and not passer:
            passer = player
        elif player_role == PocketRole.BLOCKER:
            blockers.append(player)
        elif player_role == PocketRole.RUSHER:
            rushers.append(player)

    # If no passer was found, raise an error.
    if not passer:
        raise InvalidPocketError("No passer in frame.")

    return passer, blockers, rushers


def get_distance(a: Dict, b: Dict) -> float:
    ax, ay = a.get("x"), a.get("y")
    bx, by = b.get("x"), b.get("y")
    if ax is None or ay is None or bx is None or by is None:
        raise ValueError("Coordinates must not be null.")

    dx = abs(bx - ax)
    dy = abs(by - ay)
    return math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))


def get_location(a: Dict) -> List[float]:
    """
    this function will return the location of the player (a) on the field
    """
    ax, ay = a.get("x"), a.get("y")
    if ax is None or ay is None:
        raise ValueError("Coordinates must not be null.")

    return [ax, ay]


def convert_pff_role_to_pocket_role(raw: str) -> str:
    try:
        pff_role = PFFRole(raw)
    except ValueError:
        pff_role = PFFRole.INVALID

    pocket_role = PFF_ROLE_TO_POCKET_ROLE.get(pff_role)
    if not pocket_role:
        return PocketRole.UNKNOWN.value
    return pocket_role.value


def pocket_to_json(pocket: PocketArea) -> Dict:
    # Convert nested dataclass to dictionary.
    data = dataclasses.asdict(pocket)

    # The dataclass does not allow a None for area, but we cannot parse a
    # np.nan from a string, so if the area is np.nan, set it to None.
    if np.isnan(data["area"]):
        data["area"] = None

    # Only keep metadata fields that are not None.
    metadata = {}
    metadata_fields = data.get("metadata", {})
    for key, value in metadata_fields.items():
        if value is not None:
            metadata[key] = value
    data["metadata"] = metadata
    if not metadata:
        del data["metadata"]

    return data


def pocket_from_json(data: Dict) -> PocketArea:
    # The dataclass does not allow a None for area, but we cannot parse a
    # np.nan from a string, so if the area is None, set it to np.nan.
    area = data.get("area")
    if area is None:
        area = np.nan

    # Use metadata fields as optional keyword arguments to create metadata.
    metadata = PocketAreaMetadata(**data.get("metadata", {}))

    pocket = PocketArea(area, metadata)
    return pocket


def vertices_from_shape(shape: Polygon):
    return list(shape.exterior.coords)


def vertices_to_shape(vertices):
    return Polygon(vertices)
