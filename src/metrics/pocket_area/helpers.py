import math

from typing import Dict, List, Tuple

from src.metrics.pocket_area.base import PocketRole, InvalidPocketError


# Tuple of form (passer, blockers, rushers)
PlayerRecordsByRole = Tuple[Dict, List[Dict], List[Dict]]


def split_records_by_role(frame: List[Dict]) -> PlayerRecordsByRole:
    """Splits the players in a frame by role and returns them."""
    passer: Dict = {}
    blockers: List[Dict] = []
    rushers: List[Dict] = []

    for player in frame:
        raw_role = player.get("role")
        player_role = PocketRole(raw_role)
        # If multiple passers, only return the first passer.
        if player_role == PocketRole.PASSER and not passer:
            passer = player
        elif player_role == PocketRole.BLOCKER:
            blockers.append(player)
        elif player_role == PocketRole.RUSHER:
            rushers.append(player)

    # If no passer was found, raise an error.
    if not passer:
        raise InvalidPocketError("No passer in frame.")

    return passer, blockers, rushers


def get_distance(a: Dict, b: Dict) -> float:
    ax, ay = a.get("x"), a.get("y")
    bx, by = b.get("x"), b.get("y")
    dx = abs(bx - ax)
    dy = abs(by - ay)
    return math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
