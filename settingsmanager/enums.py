from enum import StrEnum

__all__ = (
    "SettingsChoice",
    "ALL_SETTINGS_CHOICES",
    "DEFAULT_MAP_POOL_NAMES",
    "PER_GUILD_MAP_POOL_LIMIT",
    "PER_MAP_POOL_LIMIT",
)


class SettingsChoice(StrEnum):
    GENERAL = "general"
    MAP_POOL = "map pool"


# Consts for util
ALL_SETTINGS_CHOICES = [
    SettingsChoice.GENERAL,
    SettingsChoice.MAP_POOL,
]

DEFAULT_MAP_POOL_NAMES = [
    "default - ranked",
    "default - quickmatch",
]

PER_GUILD_MAP_POOL_LIMIT = 10
PER_MAP_POOL_LIMIT = 20
