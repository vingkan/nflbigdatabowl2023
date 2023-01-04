from typing import Dict, List

from scipy.spatial import Voronoi
from shapely import Polygon

from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata
from src.metrics.pocket_area.helpers import split_records_by_role
from src.pipeline.tasks.constants import FIELD_WIDTH

FIELD_WIDTH_MIN = 0
FIELD_WIDTH_MAX = FIELD_WIDTH


def voronoi_pocket_area(players: List[Dict]) -> PocketArea:
    passer, blockers, rushers = split_records_by_role(players)

    # How much pocket depth can be behind the passer.
    pocket_max_depth_behind_passer = 1
    # How much pocket width can be to either side of the passer.
    pocket_max_side_width = 5
    min_x = max(FIELD_WIDTH_MIN, passer["x"] - (2 * pocket_max_side_width))
    max_x = min(FIELD_WIDTH_MAX, passer["x"] + (2 * pocket_max_side_width))
    # Add fake points to keep the pocket bounded.
    ghost_points = [
        # Limit pocket area behind passer. Double the max depth behind passer
        # so that the pocket boundary will fall at the midpoint.
        (passer["x"], passer["y"] - (2 * pocket_max_depth_behind_passer)),
        # Limit pocket to line of scrimmage (y = 0).
        # TODO(vinesh): Reorient tracking data so that y = 0 is L.O.S.
        (passer["x"], 0),
        # Limit pocket area to sides of passer. Double the max side width so
        # that the pocket boundary will fall at the midpoint.
        (max_x, passer["y"]),
        (min_x, passer["y"]),
    ]

    pocket_players = [passer] + blockers + rushers
    passer_idx = 0
    points = [(p["x"], p["y"]) for p in pocket_players]
    all_points = points + ghost_points

    vor = Voronoi(all_points)
    region_idx = vor.point_region[passer_idx]
    region_vertices_indices = vor.regions[region_idx]
    region_vertices = [
        (vor.vertices[idx][0], vor.vertices[idx][1])
        for idx in region_vertices_indices
    ]

    pocket = Polygon(region_vertices)
    area = pocket.area
    metadata = PocketAreaMetadata(vertices=region_vertices)
    return PocketArea(area, metadata)
