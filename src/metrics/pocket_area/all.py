from typing import Dict

from src.metrics.pocket_area.base import PocketArea, PocketAreaFunction
from src.metrics.pocket_area.passer_radius_area import get_passer_radius_area
from src.metrics.pocket_area.pocket_pb_ch_area import (
    get_passBlocker_convexHull_area,
)
from src.metrics.pocket_area.rushers_pocket_area import rushers_pocket_area
from src.metrics.pocket_area.voronoi_pocket_area import voronoi_pocket_area

POCKET_AREA_METHODS: Dict[str, PocketAreaFunction] = {
    "passer_radius": get_passer_radius_area,
    "blocker_convex_hull": get_passBlocker_convexHull_area,
    "rushers_pocket_area": rushers_pocket_area,
    "voronoi_pocket_area": voronoi_pocket_area,
}
