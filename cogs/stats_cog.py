from typing import Coroutine, Dict

from discord import app_commands
import discord
from discord.ext import commands

from event import Event, MatchFinalisedPayload
from statsmanager import StatsPlayer


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

        print("[StatsCog] Successfully loaded")

    def _player_lb_text(self, guild_id: int, player: StatsPlayer) -> str:
        return " ".join([
            f"1. {self.bot.get_guild(guild_id).get_member(player.id).display_name}",
            f"[{player.points} pts | {player.max_points} peak]",
            f"[{player.wins}W/{player.losses}L | {player.wl_ratio * 100}% WR]",
            f"[MVP x{player.times_mvp}]",
        ])

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

        content = "\n".join(["## Server Leaderboard"] + [
            self._player_lb_text(interaction.guild_id, player) for player in sorted(players, key=lambda p: p.points, reverse=True)
        ])
        await interaction.response.send_message(content=content)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
