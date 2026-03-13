import copy
from typing import Coroutine, Dict

import discord
from discord import app_commands
from discord.ext import commands

from canned import Canned
from event import Event, PlayerStatsEditPayload, PlayerStatsResetPayload
from ui import (ConfirmationModal, PlayerStatsDeleteDMView,
                PlayerStatsEditModal, PlayerStatsResetDMView, PlayerStatsEditDMView)


class PlayerCog(commands.GroupCog, name="player"):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self.send_player_stats_reset_dm: Event.PLAYER_STATS_RESET,
            self.send_player_stats_delete_dm: Event.PLAYER_STATS_DELETE,
            self.send_player_stats_edit_dm: Event.PLAYER_STATS_EDITED,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        self.bot.logger.info("[PlayerCog] Successfully loaded")

    async def send_player_stats_reset_dm(self, payload: PlayerStatsResetPayload):
        user = self.bot.get_user(payload.user_id)
        guild = self.bot.get_guild(payload.guild_id)
        if user is None or guild is None:
            return self.bot.logger.info(f"Unable to send player stats RESET DM for user_id={payload.user_id} and guild_id={payload.guild_id}")

        await user.send(view=PlayerStatsResetDMView(user=user, guild=guild))

    async def send_player_stats_delete_dm(self, payload: PlayerStatsResetPayload):
        user = self.bot.get_user(payload.user_id)
        guild = self.bot.get_guild(payload.guild_id)
        if user is None or guild is None:
            return self.bot.logger.info(f"Unable to send player stats DELETE DM for user_id={payload.user_id} and guild_id={payload.guild_id}")

        await user.send(view=PlayerStatsDeleteDMView(user=user, guild=guild))

    async def send_player_stats_edit_dm(self, payload: PlayerStatsEditPayload):
        user = self.bot.get_user(payload.user_id)
        guild = self.bot.get_guild(payload.guild_id)
        if user is None or guild is None:
            return self.bot.logger.info(f"Unable to send player stats EDIT DM for user_id={payload.user_id} and guild_id={payload.guild_id}")

        await user.send(view=PlayerStatsEditDMView(user=user, guild=guild, previous=payload.previous, new=payload.new))

    async def _perform_checks(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        # Must have manage guild permission to execute
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(Canned.ERR_PERMS, ephemeral=True)
            return False

        # Ensure specified member is not a bot user
        if member.bot:
            await interaction.response.send_message(Canned.ERR_BOT_USER, ephemeral=True)
            return False

        # Ensure there is an active season
        try:
            await self.bot.stats_manager.ensure_season(guild_id=interaction.guild_id)
        except ValueError:
            await interaction.response.send_message(Canned.ERR_SEASON_NO_EXISTS, ephemeral=True)
            return False

        # Ensure specified member has stats (is ranked)
        all_players = await self.bot.stats_manager.get_guild_players(interaction.guild_id)
        if not any([player.id == member.id for player in all_players]):
            await interaction.response.send_message(Canned.ERR_STATS_PLAYER_NO_RANKED, ephemeral=True)
            return False

        # Everything passed
        return True

    @app_commands.command(name="reset", description="Reset the stats for a player for the current active season")
    @app_commands.describe(member="The member for which stats are to be reset")
    async def _reset_command(self, interaction: discord.Interaction, member: discord.Member):
        # Must pass all checks before confirmation modal is sent
        if not await self._perform_checks(interaction, member):
            return

        # Send custom confirmation modal and wait until interaction is completed
        confirmation_modal = ConfirmationModal(operation="Reset Player Stats", custom={
            "yes": "I understand and wish to reset stats",
        })
        await interaction.response.send_modal(confirmation_modal)
        await confirmation_modal.wait()

        # Cancel if user canceled the modal or explicitly selected no
        if not confirmation_modal.proceed:
            return

        # Reset stats and send confirmation messages
        await self.bot.stats_manager.reset_player(guild_id=interaction.guild_id, user_id=member.id)
        await interaction.followup.send(f"Player {member.mention}'s stats have been successfully reset", ephemeral=True)
        self.bot.dispatch(Event.PLAYER_STATS_RESET, PlayerStatsResetPayload.create(
            user_id=member.id,
            guild_id=interaction.guild_id,
        ))

    @app_commands.command(name="delete", description="Delete the stats for a player for the current active season")
    @app_commands.describe(member="The member for which stats are to be deleted")
    async def _delete_command(self, interaction: discord.Interaction, member: discord.Member):
        # Must pass all checks before confirmation modal is sent
        if not await self._perform_checks(interaction, member):
            return

        # Send custom confirmation modal and wait until interaction is completed
        confirmation_modal = ConfirmationModal(operation="Delete Player Stats", custom={
            "yes": "I understand and wish to delete stats",
        })
        await interaction.response.send_modal(confirmation_modal)
        await confirmation_modal.wait()

        # Cancel if user canceled the modal or explicitly selected no
        if not confirmation_modal.proceed:
            return

        # Delete stats and send confirmation messages
        await self.bot.stats_manager.delete_player(guild_id=interaction.guild_id, user_id=member.id)
        await interaction.followup.send(f"Player {member.mention}'s stats have been successfully deleted", ephemeral=True)
        self.bot.dispatch(Event.PLAYER_STATS_DELETE, PlayerStatsResetPayload.create(
            user_id=member.id,
            guild_id=interaction.guild_id,
        ))

    @app_commands.command(name="edit", description="Edits the stats for a player for the current active season")
    @app_commands.describe(member="The member for which stats are to be edited")
    async def _edit_command(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._perform_checks(interaction, member):
            return

        # Check to see if player is even ranked
        ranked_players = await self.bot.stats_manager.get_guild_players(interaction.guild_id)
        player = discord.utils.find(
            lambda p: p.id == member.id, ranked_players)
        if player is None:
            return await interaction.response.send_message(Canned.ERR_STATS_PLAYER_NO_RANKED, ephemeral=True)

        # Send PlayerStatsEdit modal and wait until interaction is completed
        edit_modal = PlayerStatsEditModal(bot=self.bot, player=player)
        await interaction.response.send_modal(edit_modal)
        await edit_modal.wait()

        # Cancel if the user canceled the modal
        if not edit_modal.apply_edits:
            return await interaction.followup.send(f"Player {member.mention}'s stats were NOT edited", ephemeral=True)

        # Edit stats and send confirmation
        previous = copy.deepcopy(player)
        await interaction.followup.send(f"Player {member.mention}'s stats have been successfully edited", ephemeral=True)
        new = await self.bot.stats_manager.edit_player(
            guild_id=interaction.guild_id,
            user_id=member.id,
            new_stats=edit_modal.new_stats,
        )
        self.bot.dispatch(Event.PLAYER_STATS_EDITED, PlayerStatsEditPayload.create(
            user_id=member.id,
            guild_id=interaction.guild_id,
            previous=previous,
            new=new,
        ))


async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
