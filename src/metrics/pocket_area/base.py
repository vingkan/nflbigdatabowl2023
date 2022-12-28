from enum import Enum
from typing import Callable, Dict, List


class PocketRole(Enum):
    PASSER = "passer"
    BLOCKER = "blocker"
    RUSHER = "rusher"
    UNKNOWN = "unknown"


class PFFRole(Enum):
    PASS = "Pass"  # nosec
    PASS_ROUTE = "Pass Route"  # nosec
    PASS_BLOCK = "Pass Block"  # nosec
    PASS_RUSH = "Pass Rush"  # nosec
    COVERAGE = "Coverage"
    FOOTBALL = "Football"
    INVALID = "Invalid"


PFF_ROLE_TO_POCKET_ROLE: Dict[PFFRole, PocketRole] = {
    PFFRole.PASS: PocketRole.PASSER,
    PFFRole.PASS_BLOCK: PocketRole.BLOCKER,
    PFFRole.PASS_RUSH: PocketRole.RUSHER,
}

# Type hint for functions that compute pocket area
PocketAreaFunction = Callable[[List[Dict]], float]


class InvalidPocketError(Exception):
    pass
