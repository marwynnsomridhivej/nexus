from typing import List, Tuple, Union

from base import WrapperBase
from matchmanager import MatchEntry, MatchTeam
from queuemanager import QueueEntry

__all__ = (
    "QueueFilledPayload",

    "PrematchPayload",

    "VCPayload",
    "VCResetPayload",

    "MatchFinalisedPayload",
)


class QueueFilledPayload(WrapperBase):
    slots = (
        "__guild_id",
        "__name",
        "__entry",
    )

    def __init__(self, data: dict):
        self.__guild_id: int = data["guild_id"]
        self.__name: str = data["name"]
        self.__entry: QueueEntry = data["entry"]

    @property
    def guild_id(self) -> int:
        return self.__guild_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def entry(self) -> QueueEntry:
        return self.__entry

    def serialise(self) -> dict:
        return {
            "guild_id": self.__guild_id,
            "name": self.__name,
            "entry": self.__entry,
        }


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


class VCPayload(WrapperBase):
    __slots__ = (
        "__vc_listen_id",
        "__vc_dest_id",
        "__player_ids",
        "__stop",
    )

    def __init__(self, data: dict):
        self.__vc_listen_id: int = data["vc_listen_id"]
        self.__vc_dest_id: Union[int, None] = data["vc_dest_id"]
        self.__player_ids: List[int] = data["player_ids"]
        self.__stop: bool = data["stop"]

    @property
    def vc_listen_id(self) -> int:
        return self.__vc_listen_id

    @property
    def vc_dest_id(self) -> int:
        return self.__vc_dest_id

    @property
    def player_ids(self) -> List[int]:
        return self.__player_ids

    @property
    def stop(self) -> bool:
        return self.__stop

    def serialise(self) -> dict:
        return {
            "vc_listen_id": self.__vc_listen_id,
            "vc_dest_id": self.__vc_dest_id,
            "player_ids": self.__player_ids,
            "stop": self.__stop,
        }

    @classmethod
    def create_add(cls, listen_id: int, dest_id: int, player_ids: List[int]) -> "VCPayload":
        return cls.parse({
            "vc_listen_id": listen_id,
            "vc_dest_id": dest_id,
            "player_ids": player_ids,
            "stop": False,
        })

    @classmethod
    def create_remove(cls, listen_id: int, player_ids: List[int]) -> "VCPayload":
        return cls.parse({
            "vc_listen_id": listen_id,
            "vc_dest_id": None,
            "player_ids": player_ids,
            "stop": True,
        })


class VCResetPayload(WrapperBase):
    __slots__ = (
        "__guild_id",
        "__lobby_vc_id",
        "__teams",
    )

    def __init__(self, data: dict):
        self.__guild_id: int = data["guild_id"]
        self.__lobby_vc_id: int = data["lobby_vc_id"]
        self.__teams: List[MatchTeam] = data["teams"]

    @property
    def guild_id(self) -> int:
        return self.__guild_id

    @property
    def lobby_vc_id(self) -> int:
        return self.__lobby_vc_id

    @property
    def teams(self) -> List[MatchTeam]:
        return self.__teams

    def serialise(self) -> dict:
        return {
            "guild_id": self.__guild_id,
            "lobby_vc_id": self.__lobby_vc_id,
            "teams": self.__teams,
        }

    @classmethod
    def create(cls, guild_id: int, lobby_vc_id: int, teams: List[MatchTeam]) -> "VCResetPayload":
        return cls({
            "guild_id": guild_id,
            "lobby_vc_id": lobby_vc_id,
            "teams": teams,
        })


class MatchFinalisedPayload(WrapperBase):
    __slots__ = (
        "__guild_id",
        "__name",
        "__owner_id",
        "__lobby_vc_id",
        "__winning_team",
        "__losing_team",
    )

    def __init__(self, data: dict):
        self.__guild_id: int = data["guild_id"]
        self.__name: str = data["name"]
        self.__owner_id: int = data["owner_id"]
        self.__lobby_vc_id: int = data["lobby_vc_id"]
        self.__winning_team: MatchTeam = data["winning_team"]
        self.__losing_team: MatchTeam = data["losing_team"]

    @property
    def guild_id(self) -> int:
        return self.__guild_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def owner_id(self) -> int:
        return self.__owner_id

    @property
    def lobby_vc_id(self) -> int:
        return self.__lobby_vc_id

    @property
    def teams(self) -> List[MatchTeam]:
        return [self.__winning_team, self.__losing_team]

    @property
    def winning_team(self) -> MatchTeam:
        return self.__winning_team

    @property
    def losing_team(self) -> MatchTeam:
        return self.__losing_team

    def serialise(self) -> dict:
        return {
            "guild_id": self.__guild_id,
            "name": self.__name,
            "owner_id": self.__owner_id,
            "lobby_vc_id": self.__lobby_vc_id,
            "winning_team": self.__winning_team,
            "losing_team": self.__losing_team,
        }

    @classmethod
    def create(cls, *, guild_id: int, name: str, owner_id: int, match_entry: MatchEntry) -> "MatchFinalisedPayload":
        return cls({
            "guild_id": guild_id,
            "name": name,
            "owner_id": owner_id,
            "lobby_vc_id": match_entry.voice_channel_id,
            "winning_team": match_entry.winning_team,
            "losing_team": match_entry.losing_team,
        })
