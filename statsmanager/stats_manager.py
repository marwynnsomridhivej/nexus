import copy
from typing import List, Tuple

import discord

from base import ManagerBase
from exceptions import PlayerDoesNotExist
from matchmanager import MatchTeam

from .stats import *

__all__ = (
    "StatsManager",
)


class StatsManager(ManagerBase):
    def __init__(self, stats_loc: str):
        super().__init__(stats_loc, "stats")

    async def load(self) -> None:
        await super().load(name="StatsManager")

    # =====================================
    # ============PLAYERS STUFF============
    # =====================================
    async def _get_or_create_wrapper(self) -> StatsWrapper:
        return await super()._get_or_create_wrapper(cls=StatsWrapper)

    async def get_or_create_player(self, *, guild_id: int, user_id: int) -> StatsPlayer:
        wrapper = await self._get_or_create_wrapper()
        sgc = wrapper.get_or_create(guild_id)

        try:
            player = sgc.current.get_player(user_id, throw=True)
        except PlayerDoesNotExist:
            player = sgc.current.create_player(user_id)
            await self.write(wrapper)

        return player

    async def get_guild_players(self, guild_id: int) -> List[StatsPlayer]:
        wrapper = await self._get_or_create_wrapper()
        return [player for player in wrapper.get_or_create(guild_id).current.players.values()]

    async def reset_player(self, *, guild_id: int, user_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).current.get_player(
            user_id, throw=True).reset()
        await self.write(wrapper)

    async def delete_player(self, *, guild_id: int, user_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).current.delete_player(user_id)
        await self.write(wrapper)

    async def award_team(self, *, guild_id: int, team: MatchTeam):
        wrapper = await self._get_or_create_wrapper()
        for player_id in team.players:
            wrapper.get_or_create(guild_id).current.award_player(
                player_id, team.mvp_id, team.win)
        await self.write(wrapper)

    # =====================================
    # ============SEASONS STUFF============
    # =====================================
    async def ensure_season(self, *, guild_id: int) -> None:
        """Ensures the specified guild has an active season, or if the named one exists

        Args:
            guild_id (int): The ID of the guild

        Raises:
            ValueError: No active season exists for the specified guild
        """
        wrapper = await self._get_or_create_wrapper()
        exists = wrapper.get(guild_id, throw=True).has_active_season()
        err = ValueError(f"No active season for guild ID {guild_id}")
        if not exists:
            raise err

    async def start_season(self, *, guild_id: int, name: str) -> StatsSeason:
        wrapper = await self._get_or_create_wrapper()
        sgc = wrapper.get_or_create(guild_id)
        sgc.set_current_season(name)
        await self.write(wrapper)
        return sgc.current

    async def stop_season(self, *, guild_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).stop_current_season()
        await self.write(wrapper)

    async def get_season(self, *, guild_id: int, name: str = None) -> StatsSeason:
        wrapper = await self._get_or_create_wrapper()
        sgc = wrapper.get_or_create(guild_id)

        # If no name specified, return current season details
        if name is None:
            return sgc.current

        # Find first instance of season which matches the specified name
        seasons = copy.deepcopy(sgc.history)
        if isinstance(sgc.current, StatsSeason):
            seasons.insert(0, sgc.current)
        return discord.utils.find(lambda s: s.name == name, seasons)

    async def get_season_rankings(self, *, guild_id: int, name: str = None) -> List[Tuple[int, StatsPlayer]]:
        wrapper = await self._get_or_create_wrapper()
        sgc = wrapper.get_or_create(guild_id)

        # Get appropriate season
        if name is None:
            season = sgc.current
        else:
            name = name.lower()
            seasons = copy.deepcopy(sgc.history)
            if isinstance(sgc.current, StatsSeason):
                seasons.insert(0, sgc.current)
            season = discord.utils.find(
                lambda s: s.name == name, seasons)

        # If season not found and name was specified, raise ValueError
        if season is None:
            raise ValueError(
                f"No season exists with the name \"{name}\"")

        players = [
            p for p in season.players.values()
        ]

        # Sort player list by highest to lowest by points
        # Point tiebreak handled by win loss ratio
        # Win loss ratio tiebreak handled by matches played
        players.sort(key=lambda p: (p.points, p.times_mvp,
                     p.wl_ratio, p.matches_played), reverse=True)

        previous_points = None
        previous_rank = None
        rank_ordered = []
        for rank, player in enumerate(players, 1):
            # Initialise the previous point count if not set
            if previous_points is None:
                previous_points = player.points

            # Initialise the previous rank if not set
            if previous_rank is None:
                previous_rank = rank

            # Check if current player has same points as previous. If so, reuse previous rank number
            if player.points == previous_points:
                rank_ordered.append((previous_rank, player))
                continue

            # Otherwise, append true rank and player, update previous points and rank
            rank_ordered.append((rank, player))
            previous_points = player.points
            previous_rank = rank

        return rank_ordered

    async def get_all_seasons(self, guild_id: int) -> List[StatsSeason]:
        wrapper = await self._get_or_create_wrapper()

        current = wrapper.get_or_create(guild_id).current
        seasons = copy.deepcopy(wrapper.get_or_create(guild_id).history)
        if isinstance(current, StatsSeason):
            seasons.insert(0, current)

        return seasons

    async def increment_season_match_count(self, guild_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).current.match_count += 1
        await self.write(wrapper)
