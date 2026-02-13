import json
import os
from datetime import datetime
from typing import Dict, Optional

import discord
from aiofile import async_open

from exceptions import *

from .queue import Queue, QueueEntry
from .queue_type import QueueType

MAX_PLAYERS = {
    QueueType.R6_5V5: 10,
    QueueType.R6_1V1: 2,
}


class QueueManager(object):
    def __init__(self, queue_loc: str):
        self.__queue_loc = queue_loc
        self.queues_file_path = f"{self.__queue_loc}/queues.json"

    async def load(self):
        if not os.path.exists(self.__queue_loc):
            os.mkdir(self.__queue_loc)

        await self._get_or_create_queue()
        print("[QueueManager] Successfully loaded")

    async def __get_queue(self) -> dict:
        if os.path.exists(self.queues_file_path):
            async with async_open(self.queues_file_path, "r") as afile:
                return json.loads(await afile.read())

        raise NoQueuesFile(self.queues_file_path)

    async def __write_queue_file(self, queue: Queue) -> None:
        async with async_open(self.queues_file_path, "w") as afile:
            await afile.write(json.dumps(queue.serialise(), indent=4))

    async def _get_or_create_queue(self) -> Queue:
        try:
            data = await self.__get_queue()
        except NoQueuesFile:
            async with async_open(self.queues_file_path, "w") as afile:
                await afile.write(json.dumps({}))
            data = {}
        return Queue.parse(data)

    async def create_queue(self, *, guild_id: int, owner_id: int, name: str, queue_type: QueueType) -> None:
        queue = await self._get_or_create_queue()
        queue_entry_data = {
            "owner_id":     owner_id,
            "created_date": datetime.now().strftime(r"%d/%m/%Y, %H:%M:%S"),
            "type":         queue_type,
            "players":      [],
            "max_players":  MAX_PLAYERS.get(queue_type),
            "locked": False,
            "in_progress": False,
        }
        queue.get_or_create(guild_id).create(name.lower(), queue_entry_data)
        await self.__write_queue_file(queue)

    async def delete_queue(self, guild_id: int, name: str, user_id: int) -> None:
        queue = await self._get_or_create_queue()
        queue.get_or_create(guild_id).delete(name, user_id)
        await self.__write_queue_file(queue)

    async def join_user_to_queue(self, guild_id: int, user_id: int, name: str) -> None:
        queue = await self._get_or_create_queue()
        queue.get_or_create(guild_id)\
            .get(name.lower(), throw=True)\
            .add_player(user_id)
        await self.__write_queue_file(queue)

    async def leave_user_from_queue(self, guild_id: int, user_id: int, name: str) -> None:
        queue = await self._get_or_create_queue()
        queue.get_or_create(guild_id)\
            .get(name.lower(), throw=True)\
            .remove_player(user_id)
        await self.__write_queue_file(queue)

    async def set_queue_lock_state(self, guild_id: int, user_id: int, name: str, state: bool) -> None:
        queue = await self._get_or_create_queue()
        queue.get_or_create(guild_id)\
            .get(name.lower(), throw=True)\
            .set_lock(user_id, state)
        await self.__write_queue_file(queue)

    async def set_progress_state(self, guild_id: int, name: str, state: bool) -> None:
        queue = await self._get_or_create_queue()
        queue.get_or_create(guild_id)\
            .get(name.lower(), throw=True)\
            .set_progress(state)
        await self.__write_queue_file(queue)

    async def get_all_queues(self, guild_id: int) -> Dict[str, QueueEntry]:
        queue = await self._get_or_create_queue()
        return queue.get_or_create(guild_id).data

    async def list_queues(self, guild_id: int, member: Optional[discord.Member] = None, queue_type: Optional[QueueType] = None) -> Dict[str, QueueEntry]:
        queue = await self._get_or_create_queue()
        results = queue.get_or_create(guild_id).filter(
            member=member,
            queue_type=queue_type
        )
        if not results:
            raise NoListResults(member=member, queue_type=queue_type)

        return results
