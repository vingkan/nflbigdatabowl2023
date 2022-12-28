from typing import Dict, List

from src.metrics.pocket_area.base import PocketArea, PocketAreaFunction
from src.metrics.pocket_area.passer_radius_area import get_passer_radius_area


def always_zero(records: List[Dict]) -> PocketArea:
    return PocketArea(area=0)


POCKET_AREA_METHODS: Dict[str, PocketAreaFunction] = {
    "passer_radius": get_passer_radius_area,
    # TOOD(vinesh): Remove this placeholder when other methods are added.
    "zero": always_zero,
}
