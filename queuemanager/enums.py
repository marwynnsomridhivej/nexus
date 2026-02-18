from enum import StrEnum

__all__ = (
    "CaptSelect",
    "QueueType",
)


class QueueType(StrEnum):
    R6_5V5 = "Rainbow Six Siege - 5v5"
    R6_1V1 = "Rainbow Six Siege - 1v1"


class CaptSelect(StrEnum):
    RANDOM = "random"
    RATING = "rating"
    MANUAL = "manual"