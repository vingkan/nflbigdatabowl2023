from typing import List, Dict
from scipy.spatial import ConvexHull
from src.metrics.pocket_area.base import PocketArea, PocketAreaMetadata

def rushers_pocket_area(players: List[Dict]) -> PocketArea:

    points = [(p['x'], p['y']) for p in players if p['role'] == 'rusher' or p['role'] == 'passer']
    hull = ConvexHull(points)
    vertex_coords = [tuple(hull.points[idx]) for idx in hull.vertices]
    area = hull.volume
    metadata = PocketAreaMetadata(vertices=vertex_coords)
    return PocketArea(area, metadata)
