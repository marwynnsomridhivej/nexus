from typing import List

from base import ManagerBase
from exceptions import PlayerDoesNotExist

from .stats import StatsPlayer, StatsWrapper
from matchmanager import MatchTeam

__all__ = (
    "StatsManager",
)


class StatsManager(ManagerBase):
    def __init__(self, stats_loc: str):
        super().__init__(stats_loc, "stats")

    async def load(self) -> None:
        await super().load(name="StatsManager")

    async def _get_or_create_wrapper(self) -> StatsWrapper:
        return await super()._get_or_create_wrapper(cls=StatsWrapper)

    async def get_or_create_player(self, *, guild_id: int, user_id: int) -> StatsPlayer:
        wrapper = await self._get_or_create_wrapper()
        sgc = wrapper.get_or_create(guild_id)

        try:
            player = sgc.get(user_id, throw=True)
        except PlayerDoesNotExist:
            player = sgc.create(user_id)
            await self.write(wrapper)

        return player
    
    async def get_guild_players(self, guild_id: int) -> List[StatsPlayer]:
        wrapper = await self._get_or_create_wrapper()
        return [player for player in wrapper.get_or_create(guild_id).data.values()]

    async def reset_player(self, *, guild_id: int, user_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).get(user_id, throw=True).reset()
        await self.write(wrapper)

    async def delete_player(self, *, guild_id: int, user_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).delete(user_id)
        await self.write(wrapper)

    async def award_team(self, *, guild_id: int, team: MatchTeam):
        wrapper = await self._get_or_create_wrapper()
        for player_id in team.players:
            wrapper.get_or_create(guild_id).award(player_id, team.mvp_id, team.win)
        await self.write(wrapper)
