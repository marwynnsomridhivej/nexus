from typing import Dict, List, Union

from base import WrapperBase
from exceptions import *
from queuemanager import QueueType

from .enums import *

__all__ = (
    "MatchWrapper",
    "MatchGuildContainer",
    "MatchEntry",
    "MatchTeam",
)


class MatchWrapper(WrapperBase):
    __slots__ = (
        "__data",
    )

    def __init__(self, data: dict):
        self.__data: Dict[int, MatchGuildContainer] = {
            int(guild_id): MatchGuildContainer.parse(guild_containers) for guild_id, guild_containers in data.items()
        }

    def get(self, guild_id: int, throw: bool = False) -> Union["MatchGuildContainer", None]:
        """Get a MatchGuildContainer (MGC) of the specified guild

        Args:
            guild_id (int): The guild ID of the guild
            throw (bool): Whether or not to throw an exception if an MGC instance is not found

        Raises:
            InvalidGuildID: No MGC instance exists for the specified guild

        Returns:
            Union[MatchGuildContainer, None]: The MGC instance of the specified guild
        """
        mgc = self.__data.get(guild_id)
        if mgc is None and throw:
            raise InvalidGuildID(guild_id)
        return mgc

    def get_or_create(self, guild_id: int) -> "MatchGuildContainer":
        """Get or create a MatchGuildContainer (MGC) for the specified guild

        Args:
            guild_id (int): The ID of the guild

        Returns:
            MatchGuildContainer: An existing MGC instance or a newly created blank instance
        """
        mgc = self.get(guild_id)
        if mgc is None:
            mgc = MatchGuildContainer({})
            self.__data[guild_id] = mgc
        return mgc

    @property
    def data(self) -> Dict[int, "MatchGuildContainer"]:
        return self.__data

    def serialise(self) -> dict:
        """Convert MatchWrapper instance representation into a dict

        Returns:
            dict: Dictionary representation of the MatchWrapper instance
        """
        return {
            guild_id: mgc.serialise() for guild_id, mgc in self.__data.items()
        }


class MatchGuildContainer(WrapperBase):
    __slots__ = (
        "__data",
    )

    def __init__(self, data: dict):
        self.__data = {
            name: MatchEntry.parse(entry) for name, entry in data.items()
        }

    def get(self, name: str, throw: bool = False) -> Union["MatchEntry", None]:
        """Get a MatchEntry with the specified name

        Args:
            name (str): The name of the desired MatchEntry instance
            throw (bool): Whether or not to throw an exception if a MatchEntry instance is not found

        Raises:
            MatchDoesNotExist: No MatchEntry instance exists with the specified name

        Returns:
            Union[MatchEntry, None]: The MatchEntry instance with the specified name
        """
        data = self.__data.get(name)
        if data is None and throw:
            raise MatchDoesNotExist(name)
        return data

    def create(self, name: str, data: dict) -> None:
        """Create a MatchEntry with specified name and data

        Args:
            name (str): The name of the match
            data (dict): The attributes of the match

        Raises:
            MatchAlreadyExists: Exception thrown when name is already in use
        """
        if self.__data.get(name) is not None:
            raise MatchAlreadyExists(name)
        self.__data[name] = MatchEntry.parse(data)

    def delete(self, name: str) -> "MatchEntry":
        """Delete a MatchEntry with the specified name

        Args:
            name (str): The name of the match

        Raises:
            MatchDoesNotExist: No MatchEntry instance exists with the specified name

        Returns:
            MatchEntry: MatchEntry instance that has been deleted
        """
        match_entry = self.__data.get(name)
        if match_entry is None:
            raise MatchDoesNotExist(name)

        return self.__data.pop(name)

    @property
    def data(self) -> Dict[str, "MatchEntry"]:
        return self.__data

    def serialise(self) -> dict:
        """Convert MatchGuildContainer (MGC) instance representation into a dict

        Returns:
            dict: Dictionary representation of the MGC instance
        """
        return {
            name: entry.serialise() for name, entry in self.__data.items()
        }


class MatchEntry(WrapperBase):
    __slots__ = (
        "created_date",
        "type",
        "voice_channel_id",

        "team_a",
        "team_b",
        "map",
    )

    def __init__(self, data: dict):
        self.created_date: str = data["created_date"]
        self.type: QueueType = data["type"]
        self.voice_channel_id: int = data["voice_channel_id"]

        self.team_a: MatchTeam = MatchTeam.parse(data["team_a"])
        self.team_b: MatchTeam = MatchTeam.parse(data["team_b"])
        self.map: Union[R6Map, None] = data["map"]

    def get_team_of_user(self, user_id: int) -> "MatchTeam":
        """Finds the team the specified user ID belongs to

        Args:
            user_id (int): The ID of the user to search for

        Returns:
            MatchTeam: The team the user belongs to
        """
        return self.team_a if user_id in self.team_a.players else self.team_b

    def designate_winner(self, name: str) -> None:
        """Designate winner by team name. The losing team is also automatically set

        Args:
            name (str): The name of the winner

        Raises:
            MatchFinalised: The match has been finalised and results cannot be modified
        """
        if self.wins_set:
            raise MatchFinalised

        self.team_a.win = self.team_a.name == name
        self.team_b.win = not self.team_a.win

    def designate_exceptional(self, mvp_id: int) -> None:
        """Designates a team's MVP

        Args:
            mvp_id (int): The user ID of the team MVP

        Raises:
            MatchFinalised: The match has been finalised and results cannot be modified
            MVPAlreadyAssigned: The team the user is on already has an MVP assigned
        """
        if self.mvps_set:
            raise MatchFinalised

        self.get_team_of_user(mvp_id).designate(mvp_id)

    @property
    def captains(self) -> List[int]:
        return [self.team_a.captain_id, self.team_b.captain_id]

    @property
    def has_map(self) -> bool:
        return isinstance(self.map, R6Map)

    @property
    def mvps_set(self) -> bool:
        return isinstance(self.team_a.mvp_id, int) and isinstance(self.team_b.mvp_id, int)

    @property
    def wins_set(self) -> bool:
        return isinstance(self.team_a.win, bool) and isinstance(self.team_b.win, bool)

    @property
    def finalised(self) -> bool:
        return self.wins_set and self.mvps_set

    @property
    def winning_team(self) -> Union["MatchTeam", None]:
        if not self.wins_set:
            return None

        return self.team_a if self.team_a.win else self.team_b

    @property
    def losing_team(self) -> Union["MatchTeam", None]:
        if not self.wins_set:
            return None

        return self.team_a if self.team_b.win else self.team_b

    def serialise(self) -> dict:
        """Convert MatchEntry instance representation into a dict

        Returns:
            dict: Dictionary representation of the MatchEntry instance
        """
        return {
            "created_date":     self.created_date,
            "type":             self.type,
            "voice_channel_id": self.voice_channel_id,

            "team_a": self.team_a.serialise(),
            "team_b": self.team_b.serialise(),
            "map": self.map,
        }


class MatchTeam(WrapperBase):
    __slots__ = (
        "voice_channel_id",
        "captain_id",
        "players",
        "win",
        "mvp_id",
    )

    def __init__(self, data: dict):
        self.voice_channel_id: Union[int, None] = data["voice_channel_id"]
        self.captain_id: Union[int, None] = data["captain_id"]
        self.players: List[int] = data["players"]
        self.win: Union[bool, None] = data["win"]
        self.mvp_id: Union[int, None] = data["mvp_id"]

    def assign_captain(self, user_id: int) -> None:
        """Designates a captain by user ID

        Args:
            user_id (int): The ID of the user to be made captain

        Raises:
            CaptainAlreadyAssigned: A team captain has already been designated
        """
        if self.captain_id is not None:
            raise CaptainAlreadyAssigned

        self.captain_id = user_id
        self.players.append(user_id)

    def draft(self, user_id: int) -> None:
        """Drafts a player to the team by user ID

        Args:
            user_id (int): The ID of the user to be drafted

        Raises:
            CaptainNotAssigned: A team captain has not been designated yet
        """
        if self.captain_id is None:
            raise CaptainNotAssigned

        self.players.append(user_id)

    def designate(self, user_id: int) -> None:
        """Designates a player on the team as the MVP

        Args:
            user_id (int): The ID of the user to be made MVP

        Raises:
            MVPAlreadyAssigned: This team already has an MVP
        """
        if self.mvp_id is not None:
            raise MVPAlreadyAssigned

        self.mvp_id = user_id

    def serialise(self) -> dict:
        """Convert MatchTeam instance representation into a dict

        Returns:
            dict: Dictionary representation of the MatchTeam instance
        """
        return {
            "voice_channel_id": self.voice_channel_id,
            "captain_id":       self.captain_id,
            "players":          self.players,
            "win":              self.win,
            "mvp_id":           self.mvp_id,
        }

    @classmethod
    def create_empty(cls) -> "MatchTeam":
        """Creates a blank MatchTeam instance

        Returns:
            MatchTeam: The created blank instance
        """
        return cls({
            "voice_channel_id": None,
            "captain_id": None,
            "players": [],
            "win": None,
            "mvp_id": None,
        })
