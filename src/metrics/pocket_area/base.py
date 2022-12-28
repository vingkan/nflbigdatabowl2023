from enum import Enum
from typing import Dict


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


class InvalidPocketError(Exception):
    pass
