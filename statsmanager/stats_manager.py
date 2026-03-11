from typing import List, Tuple

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
    async def ensure_season(self, *, guild_id: int) -> None:
        """Ensures the specified guild has an active season

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

    async def get_season_info(self, *, guild_id: int) -> StatsSeason:
        wrapper = await self._get_or_create_wrapper()
        return wrapper.get_or_create(guild_id).current

    async def get_current_season_rankings(self, *, guild_id: int) -> List[Tuple[int, StatsPlayer]]:
        wrapper = await self._get_or_create_wrapper()
        players = [
            p for p in wrapper.get_or_create(guild_id).current.players.values()
        ]
        
        # Sort player list by highest to lowest by points
        # Point tiebreak handled by win loss ratio
        # Win loss ratio tiebreak handled by matches played
        players.sort(key=lambda p: (p.points, p.times_mvp, p.wl_ratio, p.matches_played), reverse=True)

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