from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Union

from base import WrapperBase
from exceptions import *

__all__ = (
    "StatsWrapper",
    "StatsGuildContainer",
    "StatsSeason",
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
            sgc = StatsGuildContainer.create_blank()
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
        "current",
        "history",
    )

    def __init__(self, data: dict):
        self.current: Union[StatsSeason, None] = StatsSeason.parse(
            data["current"]) if data.get("current") is not None else None
        self.history: List[StatsSeason] = [
            StatsSeason.parse(entry) for entry in data["history"]
        ]

    def has_active_season(self) -> bool:
        return isinstance(self.current, StatsSeason)

    def set_current_season(self, name: str) -> "StatsSeason":
        if self.has_active_season():
            raise ValueError("An active season already exists")

        self.current = StatsSeason.create_blank(name)

    def stop_current_season(self) -> None:
        if not self.has_active_season():
            raise ValueError("No active season exists")

        self.current.stop_season()
        self.history.append(self.current)
        self.current = None

    def serialise(self) -> dict:
        """Convert StatsGuildContainer (SGC) instance representation into a dict

        Returns:
            dict: Dictionary representation of the SGC instance
        """
        return {
            "current": self.current.serialise(),
            "history": [season.serialise() for season in self.history]
        }

    @classmethod
    def create_blank(cls) -> "StatsGuildContainer":
        return cls({
            "current": None,
            "history": [],
        })


class StatsSeason(WrapperBase):
    __slots__ = (
        "name",
        "start_timestamp",
        "end_timestamp",
        "players",
    )

    def __init__(self, data: dict):
        self.name: str = data["name"]
        self.start_timestamp: float = data["start_timestamp"]
        self.end_timestamp: float = data.get("end_timestamp", None)

        assert isinstance(data["players"], dict)
        self.players: Dict[int, StatsPlayer] = {
            int(user_id): StatsPlayer.parse(entry) for user_id, entry in data["players"].items()
        }

    @property
    def start_time_str(self) -> str:
        return datetime.fromtimestamp(self.start_timestamp).strftime(r"%d/%m/%Y")

    @property
    def end_time_str(self) -> str:
        if self.end_timestamp is None:
            return "Ongoing"
        return datetime.fromtimestamp(self.end_timestamp).strftime(r"%d/%m/%Y")

    def stop_season(self) -> None:
        self.end_timestamp = datetime.now().timestamp()

    def get_player(self, user_id: int, throw: bool = False) -> Union["StatsPlayer", None]:
        """Get a StatsPlayer with the specified name

        Args:
            name (str): The name of the desired StatsPlayer instance
            throw (bool): Whether or not to throw an exception if a StatsPlayer instance is not found

        Raises:
            PlayerDoesNotExist: No StatsPlayer instance exists with the specified name

        Returns:
            Union[StatsPlayer, None]: The StatsPlayer instance with the specified name
        """
        data = self.players.get(user_id)
        if data is None and throw:
            raise PlayerDoesNotExist(user_id)
        return data

    def create_player(self, user_id: int) -> "StatsPlayer":
        """Create a StatsPlayer with specified user_id

        Args:
            user_id (int): The ID of the user

        Raises:
            PlayerAlreadyExists: A StatsPlayer already exists for the specified user

        Returns:
            StatsPlayer: The newly created StatsPlayer instance for the specified user
        """
        if self.players.get(user_id) is not None:
            raise PlayerAlreadyExists(user_id)
        self.players[user_id] = StatsPlayer.create_zeroed(user_id)
        return self.players[user_id]

    def delete_player(self, user_id: int) -> None:
        """Deletes a player's stats entry entirely (NOT RESET)

        Args:
            user_id (int): The ID of the user

        Raises:
            PlayerDoesNotExist: No StatsPlayer exists for the specified user
        """
        if self.players.get(user_id) is None:
            raise PlayerDoesNotExist(user_id)
        del self.players[user_id]

    def award_player(self, user_id: int, mvp_id: int, win: bool) -> None:
        """Awards the specified player points for winning or losing a match

        Args:
            user_id (int): The ID of the player
            mvp_id (int): The ID of the team's MVP
            win (bool): Whether or not the player was on the winning team
        """
        try:
            player = self.get_player(user_id, throw=True)
        except PlayerDoesNotExist:
            player = self.create_player(user_id)

        func = player.win if win else player.lose
        func(user_id == mvp_id)

    def serialise(self) -> dict:
        """Convert StatsSeason instance representation into a dict

        Returns:
            dict: Dictionary representation of the StatsSeason instance
        """
        return {
            "name": self.name,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "players": {
                user_id: player.serialise() for user_id, player in self.players.items()
            }
        }

    @classmethod
    def create_blank(cls, name: str) -> "StatsSeason":
        return cls({
            "name": name,
            "start_timestamp": datetime.now().timestamp(),
            "end_timestamp": None,
            "players": {}
        })


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

        # Default point gain per win
        self.points += 2

        if mvp:
            # 1 bonus point, and MVP designation
            self.points += 1
            self.times_mvp += 1

        if self.points > self.max_points:
            self.max_points = self.points

    def lose(self, mvp: bool = False) -> None:
        """Awards a loss to the player and adjusts values accordingly

        Args:
            mvp (bool, optional): Whether or not the player was the team MVP. Defaults to False.
        """
        self.losses += 1

        # Default point loss per loss
        self.points -= 1

        if mvp:
            # Add 1 bonus point to negate the points lost, and MVP designation
            self.points += 1
            self.times_mvp += 1

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
        return Decimal("{:.2f}".format(self.wins / self.matches_played)) if self.matches_played > 0 else Decimal()

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
            "id":      user_id,
            "wins":         0,
            "losses":       0,
            "times_mvp":    0,
            "points":       0,
            "max_points":   0,
        })
