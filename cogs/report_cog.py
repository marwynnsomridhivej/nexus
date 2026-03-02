import discord
from discord import app_commands
from discord.ext import commands

from ui import *


class ReportsCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        self.bot.logger.info("[ReportsCog] Successfully loaded")

    @app_commands.command(name="feedback", description="Send feedback to the bot developer")
    async def _report_command(self, interaction: discord.Interaction):
        feedback_modal = FeedbackModal(bot=self.bot)
        await interaction.response.send_modal(feedback_modal)


async def setup(bot):
    await bot.add_cog(ReportsCog(bot))
