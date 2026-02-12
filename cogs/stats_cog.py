import os

from discord.ext import commands


class StatsCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

        self.reload()

    async def cog_load(self):
        print("[StatsCog] Successfully loaded")

    def reload(self):
        self.stats_loc = f"{self.bot.config.data_loc}/stats"

        if not os.path.exists(self.stats_loc):
            os.mkdir(self.stats_loc)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
