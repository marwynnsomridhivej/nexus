from typing import Coroutine, Dict

import discord
from discord import app_commands
from discord.ext import commands

from event import Event, MatchFinalisedPayload
from ui import LeaderboardView


class StatsCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self.calc_stats: Event.MATCH_FINALISED,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        self.bot.logger.info("[StatsCog] Successfully loaded")

    async def calc_stats(self, payload: MatchFinalisedPayload):
        for team in [payload.winning_team, payload.losing_team]:
            await self.bot.stats_manager.award_team(
                guild_id=payload.guild_id,
                team=team,
            )

    @app_commands.command(name="leaderboard", description="View the server leaderboard")
    async def _leaderboard_command(self, interaction: discord.Interaction):
        players = await self.bot.stats_manager.get_guild_players(interaction.guild_id)
        if not players:
            return await interaction.response.send_message(content="No players are currently ranked in this server", ephemeral=True)

        lbview = LeaderboardView(
            source_interaction=interaction,
            data=sorted(players, key=lambda p: p.points, reverse=True)
        )
        lbview.init_components()

        await interaction.response.send_message(
            view=lbview,
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
