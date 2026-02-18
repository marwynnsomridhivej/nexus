import asyncio
import sys

import discord
from discord.ext import commands

from config import Config
from matchmanager import MatchManager
from queuemanager import QueueManager

CRASH_ON_EXCEPTION = False


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.command_prefix),
            **kwargs
        )
        self.config = config
        self.queue_manager: QueueManager = QueueManager(self.config.data_loc)
        self.match_manager: MatchManager = MatchManager(self.config.data_loc)

        if (kwargs.get("debug", False)):
            self.add_listener(self.__delete_dms, "on_ready")

    async def setup_hook(self):
        # Initialise managers
        await self.queue_manager.load()
        await self.match_manager.load()

        # Load all cogs
        for cog in self.config.cogs:
            try:
                await self.load_extension(cog)
            except Exception as e:
                if (CRASH_ON_EXCEPTION):
                    raise e
                print(f"Couldn't load {cog} | {e}")

        # Sync slash commands
        guild = discord.Object(id=self.config.nexus_guild_id)
        # self.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def __delete_dms(self):
        await self.wait_until_ready()
        for user in self.users:
            try:
                if user.bot:
                    print(f"Skipped bot {user.name}...")
                    continue

                if user.dm_channel is None:
                    print(f"No DM Channel exists for user {user.name}, skipping")
                    continue

                print(f"Found DM Channel for user {user.name}")
                async for message in user.dm_channel.history():
                    if message.author.id == self.user.id:
                        print(f"Deleting message {message.id}")
                        await message.delete()
            except Exception as e:
                print(f"[{user.name}] {e}")


if __name__ == "__main__":
    CRASH_ON_EXCEPTION = len(sys.argv) > 1 and sys.argv[1] == "debug"
    config = Config()

    bot = Bot(config, intents=discord.Intents.all(), debug=CRASH_ON_EXCEPTION)
    bot.run(config.token)
