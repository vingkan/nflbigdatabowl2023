from typing import Dict, List

from scipy.spatial import Voronoi
from shapely import Polygon

from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata


def voronoi_pocket_area(players: List[Dict]) -> PocketArea:

    passer_idx = -1
    passer_coord = (-1, -1)
    for i, p in enumerate(players):
        if p["role"] == "passer":
            passer_idx = i
            passer_coord = (p["x"], p["y"])
            break

    points = [(p["x"], p["y"]) for p in players]
    ghost = (passer_coord[0], passer_coord[1] - 2)
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
