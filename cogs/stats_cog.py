from typing import Coroutine, Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from canned import Canned
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
    @app_commands.describe(name="The name of the season you would like to view rankings for")
    async def _leaderboard_command(self, interaction: discord.Interaction, name: Optional[str] = None):
        guild_id = interaction.guild_id

        # Ensure an active season exists if not named
        try:
            if name is not None:
                await self.bot.stats_manager.ensure_season(guild_id=guild_id)
        except ValueError:
            return await interaction.response.send_message(Canned.ERR_SEASON_NO_EXISTS, ephemeral=True)

        # Ensure we have rankings and the season isn't empty (aka stats exist)
        try:
            ranked_players = await self.bot.stats_manager.get_season_rankings(guild_id=guild_id, name=name)
        except ValueError:
            return await interaction.response.send_message(Canned.ERR_STATS_INVALID_SEASON_NAME, ephemeral=True)
        else:
            if not ranked_players:
                return await interaction.response.send_message(Canned.ERR_STATS_NO_PLAYERS, ephemeral=True)

        lbview = LeaderboardView(
            source_interaction=interaction,
            season=await self.bot.stats_manager.get_season(
                guild_id=guild_id,
                name=name.lower() if name else None
            ),
            rankings=ranked_players
        )
        lbview.init_components()

        await interaction.response.send_message(
            view=lbview,
            allowed_mentions=discord.AllowedMentions.none(),
            ephemeral=True
        )

    @_leaderboard_command.autocomplete("name")
    async def _leaderboard_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        seasons = await self.bot.stats_manager.get_all_seasons(interaction.guild_id)
        return sorted([
            app_commands.Choice(name=s.name.title(), value=s.name) for s in seasons if current.lower() in s.name
        ], key=lambda c: c.name)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
