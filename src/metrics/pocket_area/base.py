from enum import Enum


class PocketRole(Enum):
    PASSER = "passer"
    BLOCKER = "blocker"
    RUSHER = "rusher"


class InvalidPocketError(Exception):
    pass
