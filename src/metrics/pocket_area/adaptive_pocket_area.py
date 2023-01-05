from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

from src.metrics.pocket_area.base import (
    InvalidPocketError,
    PocketArea,
    PocketAreaMetadata,
)
from src.metrics.pocket_area.helpers import (
    get_distance,
    get_location,
    split_records_by_role,
)
from src.metrics.pocket_area.passer_radius_area import get_passer_radius_area
from src.metrics.pocket_area.rushers_pocket_area import rushers_pocket_area

"""
Adaptive Corvex Hull Pseudocode:

    1. Form a list of the passer, blockers, and rushers
    2. Find the rusher who is closest to the passer and the distance between them
    3. Filter out all players whose distance from the passer is greater than that distance
    4. If the filtered list has more than two players, calculate the convex hull of their coordinates and return the area
    5. If there are exactly two, calculate the area of a circle with that distance as the radius, then multiply that area by a proportion (let's say 0.25 for now) to represent the cone in front of the passer
    6. If there are fewer than two players in the filtered list raise an exception because something has gone wrong

"""


def find_closest_player_s(
    point: Dict, players: List[Dict], rusher_difference: float
):
    """Returns the closest players to the given point and the distance.

    rusher_difference : acceptable difference parameter from the closest rusher
    and any other rushers that should be considered to make the pocket
    """
    if not players:
        raise InvalidPocketError("No players in input.")

    closest_players: List[Dict] = []
    closest_distance = float("inf")

    # Find the closest rusher's distance
    for player in players:
        d = get_distance(point, player)
        if d <= (
            closest_distance + rusher_difference
        ) or closest_distance == float("inf"):
            closest_distance = d

    # Determine whether each rusher is within the rusher difference error
    for player in players:
        d = get_distance(point, player)
        if d <= (closest_distance + rusher_difference):
            closest_players.append(player)
            closest_distance = d

    return closest_players, closest_distance


def calculate_adaptive_pocket_area(frame: pd.DataFrame) -> PocketArea:

    passer, blockers, rushers = split_records_by_role(frame)
    if not rushers:
        raise InvalidPocketError("No rushers in frame to make pocket.")
    if not passer:
        raise InvalidPocketError("No passer in frame.")

    # Consider all pass rushers and the passer
    pocket_players = rushers + [passer]
    # use helper function in this file to get all the rushers that have a distance 3 yards
    # within the distance from the closest rusher to the quarterback
    closest_rushers = find_closest_player_s(passer, rushers, 3.0)

    # adjusted pocket will get all the pass rushers that make a valid pocket along with the qb
    adjusted_pocket = closest_rushers[0] + [passer]

    # If there is 2 or more valid pass rushers, get the corvex hull of the rushers and qb
    if len(closest_rushers[0]) >= 2:
        return rushers_pocket_area(adjusted_pocket)
    # If there is one valid rusher, make the radius the distance from the rusher to qb,
    # restrict the area of the pocket two 1/3rd of a circle in front of the qb, make the metadata.edge
    # variable the location of the nearest pass rusher
    else:
        pocket_area = get_passer_radius_area(adjusted_pocket)
        ex, ey = closest_rushers[0][0].get("x"), closest_rushers[0][0].get("y")
        metadata = PocketAreaMetadata(
            radius=pocket_area.metadata.radius, edge=(ex, ey)
        )
        return PocketArea(pocket_area.area / 3, metadata)