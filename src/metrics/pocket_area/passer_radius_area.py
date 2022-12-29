import math
from typing import Dict, List, Tuple

from src.metrics.pocket_area.base import (
    InvalidPocketError,
    PocketArea,
    PocketAreaMetadata,
    Point,
)
from src.metrics.pocket_area.helpers import get_distance, split_records_by_role

PlayerAndDistance = Tuple[Dict, float]


def find_closest_player(point: Dict, players: List[Dict]) -> PlayerAndDistance:
    """Returns the closest player to the given point and the distance."""
    if not players:
        raise InvalidPocketError("No players in input.")

    closest_player: Dict = {}
    closest_distance = float("inf")

    for player in players:
        d = get_distance(point, player)
        if d < closest_distance or not closest_player:
            closest_player = player
            closest_distance = d

    return closest_player, closest_distance


def get_circle_area(radius: float) -> float:
    """Calculates the area of a circle using the formula: A = pi * r^2."""
    area = math.pi * math.pow(radius, 2)
    return area


def get_passer_radius_area(frame: List[Dict]) -> PocketArea:
    """
    Estimates the pocket area as the area of a circle where the radius is the
    distance from the passer to the closest rusher.
    """
    passer, blockers, rushers = split_records_by_role(frame)
    if not rushers:
        raise InvalidPocketError("No rushers in frame.")

    closest_rusher, distance = find_closest_player(passer, rushers)
    area = get_circle_area(radius=distance)

    px, py = passer["x"], passer["y"]
    if px is None or py is None:
        raise InvalidPocketError("Missing x, y coordinates for passer.")
    center: Point = (px, py)

    metadata = PocketAreaMetadata(radius=distance, center=center)
    return PocketArea(area, metadata)
