from typing import Dict, List

from scipy.spatial import Voronoi
from shapely import Polygon

from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata
from src.metrics.pocket_area.helpers import split_records_by_role


def voronoi_pocket_area(players: List[Dict]) -> PocketArea:

    passer, blockers, rushers = split_records_by_role(players)
    pocket_players = [passer] + blockers + rushers
    passer_idx = 0

    points = [(p["x"], p["y"]) for p in pocket_players]
    # add fake point that is always 2 yards behing the passer to
    # limit the backside of the pocket
    ghost = (passer["x"], passer["y"] - 2)
    points.append(ghost)

    vor = Voronoi(points)
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
