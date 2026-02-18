import json
import os
from datetime import datetime

from aiofile import async_open

from exceptions import *

from .match import *
from .payload import PrematchPayload


class MatchManager(object):
    def __init__(self, match_loc: str):
        self.__match_loc = match_loc
        self.matches_file_path = f"{self.__match_loc}/matches.json"

    async def load(self):
        if not os.path.exists(self.__match_loc):
            os.mkdir(self.__match_loc)

        await self._get_or_create_wrapper()
        print("[MatchManager] Successfully loaded")

    async def __get_wrapper(self) -> dict:
        if os.path.exists(self.matches_file_path):
            async with async_open(self.matches_file_path, "r") as afile:
                return json.loads(await afile.read())

        raise NoMatchesFile(self.matches_file_path)

    async def __write_match_file(self, wrapper: MatchWrapper) -> None:
        async with async_open(self.matches_file_path, "w") as afile:
            await afile.write(json.dumps(wrapper.serialise(), indent=4))

    async def _get_or_create_wrapper(self) -> MatchWrapper:
        try:
            data = await self.__get_wrapper()
        except NoMatchesFile:
            async with async_open(self.matches_file_path, "w") as afile:
                await afile.write("{}")
            data = {}
        return MatchWrapper.parse(data)

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
        await self.__write_match_file(wrapper)

    async def delete_match(self, guild_id: int, name: str) -> None:
        wrapper = await self._get_or_create_wrapper()
        wrapper.get_or_create(guild_id).delete(name)
        await self.__write_match_file(wrapper)

    async def get_match(self, guild_id: int, name: str) -> MatchEntry:
        wrapper = await self._get_or_create_wrapper()
        return wrapper.get(guild_id, throw=True).get(name, throw=True)
