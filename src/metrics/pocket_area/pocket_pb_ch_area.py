from typing import Dict, List, Tuple

import numpy as np
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


def get_convex_hull(
    frame: List[Dict],
) -> Tuple[float, List[Tuple[float, float]]]:
    pocket = []
    for player in frame:
        pocket.append(get_location(player))
    pocket = np.array(pocket)
    hull = ConvexHull(pocket)
    hull_points = pocket[hull.vertices]
    vertices: List[Tuple[float, float]] = [(p[0], p[1]) for p in hull_points]
    # In 2d figures, volume is actually the area of the convex hull (area is the perimeter)
    area: float = hull.volume
    return area, vertices


def get_passBlocker_convexHull_area(frame: List[Dict]) -> PocketArea:
    """
    Estimates the pocket area as the convex hull of all the pass blockers on the field
    """
    passer, blockers, rushers = split_records_by_role(frame)
    if not blockers:
        raise InvalidPocketError("No blockers in frame to make pocket.")
    if not passer:
        raise InvalidPocketError("No passer in frame.")

    pocket_players = blockers + [passer]
    area, vertices = get_convex_hull(pocket_players)
    metadata = PocketAreaMetadata(vertices=vertices)
    return PocketArea(area, metadata)
