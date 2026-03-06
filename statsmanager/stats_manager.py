from typing import List

from base import ManagerBase
from exceptions import PlayerDoesNotExist

from .stats import *
from matchmanager import MatchTeam

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
    async def ensure_season(self, *, guild_id: int, throw_if_found: bool = False) -> None:
        """Ensures the specified guild has an active season

        Args:
            guild_id (int): The ID of the guild
            throw_if_found (bool, optional): Throw an error if a season is found. Defaults to False

        Raises:
            ValueError: No active season exists for the specified guild
            ValueError: An active season already exists for the specified guild (can only be raised if throw_if_found is True)
        """
        wrapper = await self._get_or_create_wrapper()
        exists = wrapper.get(guild_id, throw=True).has_active_season()
        err = ValueError(f"No active season for guild ID {guild_id}")
        
        # Raise if we find an active season ONLY IF throw_if_found is True
        if exists and throw_if_found:
            raise err
        
        # Default, raise if we don't find an active season
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
