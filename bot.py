import asyncio
import sys

import discord
from discord.ext import commands

from config import Config

intents = discord.Intents.all()
config = Config()


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.command_prefix),
            **kwargs
        )
        self.config = config

    async def setup_hook(self):
        guild = discord.Object(id=self.config.nexus_guild_id)
        # self.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


async def main(crash_on_exception: bool = False):
    bot = Bot(config=config, intents=intents)
    for cog in config.cogs:
        try:
            await bot.load_extension(cog)
        except Exception as e:
            if (crash_on_exception):
                raise
            print(f"Couldn't load {cog} | {e}")
    try:
        await bot.start(config.token)
    except KeyboardInterrupt:
        await bot.close()


if __name__ == "__main__":
    should_crash = len(sys.argv) > 1 and sys.argv[1] == "debug"
    asyncio.run(main(crash_on_exception=should_crash))
