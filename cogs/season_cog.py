import discord
from discord import app_commands
from discord.ext import commands

from canned import Canned
from ui import ConfirmationModal, SeasonStartModal


class SeasonCog(commands.GroupCog, name="season"):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        self.bot.logger.info("[SeasonCog] Successfully loaded")

    def _ensure_perms(self, interaction: discord.Interaction) -> bool:
        # Make sure user has "manage server" permissions
        return interaction.user.guild_permissions.manage_guild

    @app_commands.command(name="start", description="Starts a new season")
    async def _start_season(self, interaction: discord.Interaction):
        if not self._ensure_perms(interaction):
            return await interaction.response.send_message(Canned.ERR_PERMS, ephemeral=True)

        try:
            # Send an error message if a season already exists
            await self.bot.stats_manager.ensure_season(
                guild_id=interaction.guild_id,
                throw_if_found=True
            )
        except ValueError:
            return await interaction.response.send_message(Canned.ERR_SEASON_EXISTS, ephemeral=True)

        season_start_modal = SeasonStartModal(bot=self.bot)
        await interaction.response.send_modal(season_start_modal)
        await season_start_modal.wait()

        # Start a season in the guild with the specified name
        await self.bot.stats_manager.start_season(
            guild_id=interaction.guild_id,
            name=season_start_modal.name
        )

    @app_commands.command(name="stop", description="Stops the current active season")
    async def _stop_season(self, interaction: discord.Interaction):
        if not self._ensure_perms(interaction):
            return await interaction.response.send_message(Canned.ERR_PERMS, ephemeral=True)

        try:
            await self.bot.stats_manager.ensure_season(guild_id=interaction.guild_id)
        except ValueError:
            return await interaction.response.send_message(Canned.ERR_SEASON_NO_EXISTS, ephemeral=True)

        season_end_modal = ConfirmationModal(operation="Stop Season")
        await interaction.response.send_modal(season_end_modal)
        await season_end_modal.wait()

        # Don't proceed if they cancel
        if not season_end_modal.proceed:
            return

        if await self.bot.match_manager.has_running_match(interaction.guild_id):
            await interaction.response.send_message(Canned.ERR_SEASON_MIP, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SeasonCog(bot))
