from discord.ext import commands

from queuemanager import QueueEntry


class MatchCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

        # Register all custom events
        @bot.event
        async def on_queue_manager_queue_full(queue_entry: QueueEntry):
            pass

    async def cog_load(self):
        print("[MatchCog] Successfully loaded")


async def setup(bot):
    await bot.add_cog(MatchCog(bot))
