from typing import Tuple, Union

from base import WrapperBase
from queuemanager import QueueEntry

__all__ = (
    "PrematchPayload",
)


class PrematchPayload(WrapperBase):
    __slots__ = (
        "__guild_id",
        "__match_name",
        "__voice_channel_id",
        "__text_channel_id",
        "__captain_select_option",
        "__captains",
        "__entry",
    )

    def __init__(self, data: dict):
        self.__guild_id: int = data["guild_id"]
        self.__match_name: str = data["match_name"]
        self.__voice_channel_id: int = data["voice_channel_id"]
        self.__text_channel_id: int = data["text_channel_id"]
        self.__captains: Tuple[int, int] = data["captains"]
        self.__entry: QueueEntry = data["entry"]

    @property
    def guild_id(self) -> int:
        return self.__guild_id

    @property
    def match_name(self) -> str:
        return self.__match_name

    @property
    def voice_channel_id(self) -> int:
        return self.__voice_channel_id

    @property
    def text_channel_id(self) -> int:
        return self.__text_channel_id

    @property
    def captains(self) -> Tuple[int, int]:
        return self.__captains

    @property
    def entry(self) -> QueueEntry:
        return self.__entry

    def serialise(self) -> dict:
        return {
            "guild_id": self.__guild_id,
            "match_name": self.__match_name,
            "voice_channel_id": self.__voice_channel_id,
            "text_channel_id": self.__text_channel_id,
            "captains": self.__captains,
            "entry": self.__entry,
        }

    def __str__(self) -> str:
        params = [
            f"guild_id={self.guild_id}",
            f"match_name={self.match_name}",
            f"voice_channel_id={self.voice_channel_id}",
            f"text_channel_id={self.text_channel_id}",
            f"captains={self.captains}",
            f"entry={self.entry}"
        ]
        return f"PrematchPayload[{", ".join(params)}]"
