from datetime import datetime

from base import ManagerBase
from exceptions import *

from .match import *
from .payload import PrematchPayload


class MatchManager(ManagerBase):
    def __init__(self, match_loc: str):
        super().__init__(match_loc, "matches")

    async def load(self):
        await super().load(name="MatchManager")

    async def _get_or_create_wrapper(self) -> MatchWrapper:
        return await super()._get_or_create_wrapper(cls=MatchWrapper)

    async def create_match(self, *, payload: PrematchPayload) -> None:
        wrapper = await self._get_or_create_wrapper()

        # Init teams
        team_a = MatchTeam.create_empty()
        team_b = MatchTeam.create_empty()

        # Assign captains
        team_a.assign_captain(payload.captains[0])
        team_b.assign_captain(payload.captains[1])

        # Craft entry data
        match_entry_data = {
            "created_date": datetime.now().strftime(r"%d/%m/%Y, %H:%M:%S"),
            "type": payload.entry.type,
            "voice_channel_id": payload.voice_channel_id,

            "team_a": team_a.serialise(),
            "team_b": team_b.serialise(),
            "map": None,
        }

        # Create match entry
        wrapper.get_or_create(payload.guild_id).create(
            payload.match_name,
            match_entry_data,
        )

        # Write to disk
        await self.write(wrapper)

    async def delete_match(self, guild_id: int, name: str) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).delete(name)
        await self.write(wrapper)

    async def get_match(self, guild_id: int, name: str) -> MatchEntry:
        wrapper = await self._get_or_create_wrapper()
        return wrapper.get(guild_id, throw=True).get(name, throw=True)

    async def draft(self, guild_id: int, name: str, captain_id: int, player_id: int) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get(guild_id, throw=True)\
            .get(name, throw=True)\
            .get_team_of_user(captain_id)\
            .draft(player_id)
        await self.write(wrapper)

    async def reset_draft(self, guild_id: int, name: str) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get(guild_id, throw=True)\
            .get(name, throw=True)\
            .reset_draft()
        await self.write(wrapper)
