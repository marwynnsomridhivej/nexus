from enum import StrEnum
from typing import List

__all__ = (
    "R6Map",

    "R6_RANKED",
    "R6_QUICKMATCH",
    "R6_TDM",
    "R6_DUAL_FRONT",

    "R6ViewOption",
)


class R6Map(StrEnum):
    # fmt: off
    BORDER: str     = "border"
    DISTRICT: str   = "district"
    BANK: str       = "bank"
    KAFE: str       = "kafe_dostoyevsky"
    CHALET: str     = "chalet"
    CLUBHOUSE: str  = "clubhouse"
    ALPHA: str      = "stadium_alpha"
    BRAVO: str      = "stadium_bravo"
    LAIR: str       = "lair"
    NIGHTHAVEN: str = "nighthaven_labs"
    CQ: str         = "close_quarter"
    EMERALD: str    = "emerald_plains"
    COASTLINE: str  = "coastline"
    CONSULATE: str  = "consulate"
    FAVELA: str     = "favela"
    FORTRESS: str   = "fortress"
    HEREFORD: str   = "hereford_base"
    HOUSE: str      = "house"
    KANAL: str      = "kanal"
    OREGON: str     = "oregon"
    OUTBACK: str    = "outback"
    PLANE: str      = "presidential_plane"
    SKYSCRAPER: str = "skyscraper"
    THEMEPARK: str  = "themepark"
    TOWER: str      = "tower"
    VILLA: str      = "villa"
    YACHT: str      = "yacht"
    # fmt: on


R6_RANKED: List[str] = sorted([
    R6Map.BORDER,
    R6Map.BANK,
    R6Map.KAFE,
    R6Map.CHALET,
    R6Map.CLUBHOUSE,
    R6Map.LAIR,
    R6Map.NIGHTHAVEN,
    R6Map.COASTLINE,
    R6Map.CONSULATE,
    R6Map.FORTRESS,
    R6Map.KANAL,
    R6Map.OREGON,
    R6Map.OUTBACK,
    R6Map.SKYSCRAPER,
    R6Map.THEMEPARK,
    R6Map.VILLA,
])

R6_QUICKMATCH: List[str] = sorted(R6_RANKED + [
    R6Map.ALPHA,
    R6Map.BRAVO,
    R6Map.EMERALD,
    R6Map.FAVELA,
    R6Map.HOUSE,
    R6Map.PLANE,
    R6Map.TOWER,
    R6Map.YACHT,
])

R6_TDM: List[str] = sorted([
    R6Map.BORDER,
    R6Map.CLUBHOUSE,
    R6Map.ALPHA,
    R6Map.LAIR,
    R6Map.NIGHTHAVEN,
    R6Map.CQ,
    R6Map.CONSULATE,
    R6Map.SKYSCRAPER,
    R6Map.THEMEPARK,
    R6Map.VILLA,
])

R6_DUAL_FRONT: List[str] = sorted([
    R6Map.DISTRICT,
])


# Sanity checks
for category in [R6_RANKED, R6_QUICKMATCH, R6_TDM, R6_DUAL_FRONT]:
    for _map in category:
        assert category.count(_map) == 1


class R6ViewOption(StrEnum):
    # Team draft by captains
    DRAFT_A = "draft_a"
    DRAFT_B = "draft_b"

    # Map ban by captains
    MAP_BAN_A = "map_a"
    MAP_BAN_B = "map_b"

    # End of match MVP designation by captains
    MVP_A = "mvp_a"
    MVP_B = "mvp_b"

    # End of match summary and finalisation by queue owner
    EOM = "set_match_result"
