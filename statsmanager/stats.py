from decimal import Decimal
from typing import Dict, List, Union

from base import WrapperBase
from exceptions import *

__all__ = (
    "StatsWrapper",
    "StatsGuildContainer",
    "StatsPlayer",
)


class StatsWrapper(WrapperBase):
    __slots__ = (
        "__data",
    )

    def __init__(self, data: dict):
        self.__data: Dict[int, StatsGuildContainer] = {
            int(guild_id): StatsGuildContainer.parse(guild_containers) for guild_id, guild_containers in data.items()
        }

    def get(self, guild_id: int, throw: bool = False) -> Union["StatsGuildContainer", None]:
        """Get a StatsGuildContainer (SGC) of the specified guild

        Args:
            guild_id (int): The guild ID of the guild
            throw (bool): Whether or not to throw an exception if a SGC instance is not found

        Raises:
            InvalidGuildID: No SGC instance exists for the specified guild

        Returns:
            Union[StatsGuildContainer, None]: The SGC instance of the specified guild
        """
        sgc = self.__data.get(guild_id)
        if sgc is None and throw:
            raise InvalidGuildID(guild_id)
        return sgc

    def get_or_create(self, guild_id: int) -> "StatsGuildContainer":
        """Get or create a StatsGuildContainer (SGC) for the specified guild

        Args:
            guild_id (int): The ID of the guild

        Returns:
            StatsGuildContainer: An existing SGC instance or a newly created blank instance
        """
        sgc = self.get(guild_id)
        if sgc is None:
            sgc = StatsGuildContainer({})
            self.__data[guild_id] = sgc
        return sgc

    @property
    def data(self) -> Dict[int, "StatsGuildContainer"]:
        return self.__data

    def serialise(self) -> dict:
        """Convert StatsWrapper instance representation into a dict

        Returns:
            dict: Dictionary representation of the StatsWrapper instance
        """
        return {guild_id: entry.serialise() for guild_id, entry in self.__data.items()}


class StatsGuildContainer(WrapperBase):
    __slots__ = (
        "__data",
    )

    def __init__(self, data: dict):
        self.__data: Dict[int, StatsPlayer] = {
            int(user_id): StatsPlayer.parse(entry) for user_id, entry in data.items()
        }

    def get(self, user_id: int, throw: bool = False) -> Union["StatsPlayer", None]:
        """Get a StatsPlayer with the specified name

        Args:
            name (str): The name of the desired StatsPlayer instance
            throw (bool): Whether or not to throw an exception if a StatsPlayer instance is not found

        Raises:
            PlayerDoesNotExist: No StatsPlayer instance exists with the specified name

        Returns:
            Union[StatsPlayer, None]: The StatsPlayer instance with the specified name
        """
        data = self.__data.get(user_id)
        if data is None and throw:
            raise PlayerDoesNotExist(user_id)
        return data

    def create(self, user_id: int) -> None:
        """Create a StatsPlayer with specified user_id

        Args:
            user_id (int): The ID of the user

        Raises:
            PlayerAlreadyExists: A StatsPlayer already exists for the specified user
        """
        if self.__data.get(user_id) is not None:
            raise PlayerAlreadyExists(user_id)
        self.__data[user_id] = StatsPlayer.create_zeroed(user_id)

    def delete(self, user_id: int) -> None:
        """Deletes a player's stats entry entirely (NOT RESET)

        Args:
            user_id (int): The ID of the user

        Raises:
            PlayerDoesNotExist: No StatsPlayer exists for the specified user
        """
        if self.__data.get(user_id) is None:
            raise PlayerDoesNotExist(user_id)
        del self.__data[user_id]

    @property
    def players(self) -> List["StatsPlayer"]:
        return [player for player in self.__data.values()]

    @property
    def data(self) -> Dict[int, "StatsPlayer"]:
        return self.__data

    def serialise(self) -> dict:
        """Convert StatsGuildContainer (SGC) instance representation into a dict

        Returns:
            dict: Dictionary representation of the SGC instance
        """
        return {user_id: entry.serialise() for user_id, entry in self.__data.items()}


class StatsPlayer(WrapperBase):
    __slots__ = (
        "id",
        "wins",
        "losses",
        "times_mvp",
        "points",
        "max_points",
    )

    def __init__(self, data: dict):
        self.id: int = data["id"]
        self.wins: int = data["wins"]
        self.losses: int = data["losses"]
        self.times_mvp: int = data["times_mvp"]
        self.points: int = data["points"]
        self.max_points: int = data["max_points"]

    def win(self, mvp: bool = False) -> None:
        """Awards a win to the player and adjusts values accordingly

        Args:
            mvp (bool, optional): Whether or not the player was the team MVP. Defaults to False.
        """
        self.wins += 1
        self.points += 5 if mvp else 2

    def lose(self, mvp: bool = False) -> None:
        """Awards a loss to the player and adjusts values accordingly

        Args:
            mvp (bool, optional): Whether or not the player was the team MVP. Defaults to False.
        """
        self.losses += 1
        self.points -= 1 if mvp else 2

    def reset(self) -> None:
        """Reset a player's win, loss, mvp, and points data
        """
        self.wins = 0
        self.losses = 0
        self.times_mvp = 0
        self.points = 0
        self.max_points = 0

    @property
    def matches_played(self) -> int:
        return self.wins + self.losses

    @property
    def wl_ratio(self) -> Decimal:
        return Decimal("{:.2f}".format(self.wins / self.losses))

    def serialise(self) -> dict:
        """Convert StatsPlayer instance representation into a dict

        Returns:
            dict: Dictionary representation of the StatsPlayer instance
        """
        return {
            "id":           self.id,
            "wins":         self.wins,
            "losses":       self.losses,
            "times_mvp":    self.times_mvp,
            "points":       self.points,
            "max_points":   self.max_points,
        }

    @classmethod
    def create_zeroed(cls, user_id: int) -> "StatsPlayer":
        """Creates a zeroed StatsPlayer instance

        Args:
            user_id (int): The ID of the user

        Returns:
            StatsPlayer: The created zeroed instance
        """
        return cls.parse({
            "user_id":      user_id,
            "wins":         0,
            "losses":       0,
            "times_mvp":    0,
            "points":       0,
            "max_points":   0,
        })
