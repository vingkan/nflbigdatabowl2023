from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial import ConvexHull
from shapely import Polygon

from src.metrics.pocket_area.base import (
    InvalidPocketError,
    PocketArea,
    PocketAreaMetadata,
)
from src.metrics.pocket_area.helpers import (
    get_distance,
    get_location,
    split_records_by_role,
    vertices_from_shape,
)
from src.pipeline.tasks.constants import FIELD_WIDTH


def limit_vertices_to_line_of_scrimmage(
    vertices: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    # If y coordinates do not cross line of scrimmage, no changes needed.
    max_y = max([p[1] for p in vertices])
    if max_y <= 0:
        return vertices

    # Create crop box to cut off area above line of scrimmage.
    # Use double the width of the field to ensure full crop.
    min_x = -1 * FIELD_WIDTH
    max_x = FIELD_WIDTH
    crop = [
        (min_x, 0),
        (max_x, 0),
        (max_x, max_y),
        (min_x, max_y),
    ]

    # Crop area past line of scrimmage.
    crop_rect = Polygon(crop)
    polygon = Polygon(vertices)
    pocket = polygon.difference(crop_rect)

    # Return vertices for cropped pocket.
    cropped_vertices = vertices_from_shape(pocket)
    return cropped_vertices


def get_convex_hull(
    frame: List[Dict],
) -> Tuple[float, List[Tuple[float, float]]]:
    pocket = []
    for player in frame:
        pocket.append(get_location(player))
    pocket = np.array(pocket)
    hull = ConvexHull(pocket)
    hull_points = pocket[hull.vertices]
    hull_vertices: List[Tuple[float, float]] = [
        (p[0], p[1]) for p in hull_points
    ]

    # Make sure the pocket does not extend past the line of scrimmage.
    vertices = limit_vertices_to_line_of_scrimmage(hull_vertices)

    # For consistency, always use Shapely to compute polygon area, in case the
    # vertices were cropped.
    hull_polygon = Polygon(vertices)
    area = hull_polygon.area
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
