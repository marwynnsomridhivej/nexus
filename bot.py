import logging
import logging.handlers
import sys
from datetime import datetime

import discord
from discord.ext import commands

from config import Config
from dmmanager import DMManager
from matchmanager import MatchManager
from queuemanager import QueueManager
from statsmanager import StatsManager


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.command_prefix),
            **kwargs
        )

        # Configuration from config.json
        self.config = config

        # Get and store root logger
        self.logger = logging.getLogger()

        # Managers for IO
        self.dm_manager: DMManager = DMManager(self.config.data_dir, self)
        self.match_manager: MatchManager = MatchManager(self.config.data_dir)
        self.queue_manager: QueueManager = QueueManager(self.config.data_dir)
        self.stats_manager: StatsManager = StatsManager(self.config.data_dir)

    async def setup_hook(self):
        # Initialise managers
        await self.dm_manager.load()
        await self.match_manager.load()
        await self.queue_manager.load()
        await self.stats_manager.load()

        # Load all cogs
        for cog in self.config.cogs:
            try:
                await self.load_extension(cog)
            except Exception as e:
                self.logger.error(f"Could not load cog {cog}: {e}")
                raise e

        # Sync slash commands
        guild = discord.Object(id=self.config.nexus_guild_id)
        # self.tree.clear_commands(guild=guild)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        await self.wait_until_ready()
        await self.dm_manager.purge_all()


if __name__ == "__main__":
    # Check if debug flag is set
    debug = len(sys.argv) > 1 and sys.argv[1].lower() == "debug"

    # Load bot config from disk
    config = Config()

    # Create root logger and set logging level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create rotating file and stream handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{config.log_dir}/{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.log",
        maxBytes=16 * 1024 * 1024,  # 16 MiB
        backupCount=10,
    )
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)

    # Set formatter and add handler to root logger
    for handler in [file_handler, stdout_handler]:
        # For type hint
        assert isinstance(handler, logging.Handler)
        handler.setFormatter(logging.Formatter(
            "[{asctime}] [{levelname}] {name}: {message}",
            r"%Y-%m-%d %H:%M:%S",
            style="{"
        ))
        logger.addHandler(handler)

    # Run bot
    bot = Bot(config, intents=discord.Intents.all())
    bot.run(config.token, log_handler=None)
