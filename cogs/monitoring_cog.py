import traceback
from typing import Coroutine, Dict, List

import discord
from discord.ext import commands

from event import *
from matchmanager import MatchTeam


class MonitoringCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self.reset_button_vc_move: Event.RESET_BUTTON_PRESSED,
            self.queue_match_cleanup: Event.MATCH_FINALISED,
            self.delete_vcs: Event.MATCH_FINALISED,
            self.delete_dms: Event.MATCH_FINALISED,
            self.explicit_delete_dms: Event.PREMATCH_DM_DELETE,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        self.bot.logger.info("[MonitoringCog] Successfully loaded")

    async def _move_team_to_lobby_vc(self, guild_id: int, lobby_vc_id: int, team: MatchTeam, reason: Reason) -> None:
        lobby_vc_channel = self.bot.get_channel(lobby_vc_id)

        # Try to move all the players in the team back to the "lobby VC"
        for player_id in team.players:
            member = self.bot\
                .get_guild(guild_id)\
                .get_member(player_id)
            if not isinstance(member, discord.Member):
                continue
            await member.move_to(lobby_vc_channel, reason=reason)

    async def _delete_dms(self, guild_id: int, players: List[int]) -> None:
        for player in players:
            try:
                message_id = await self.bot.dm_manager.delete(
                    guild_id, player)
                dm_channel = await self.bot.get_user(player).create_dm()
                await dm_channel.get_partial_message(message_id).delete()
                self.bot.logger.info(
                    f"Deleted message ID {message_id} for user {player}")
            except KeyError:
                self.bot.logger.info(
                    f"Message does not exist for guild_id {guild_id} user_id {player}")
            except discord.NotFound:
                self.bot.logger.info(
                    f"Message ID {message_id} for user {player} was already deleted")
            except discord.HTTPException as e:
                self.bot.logger.error(
                    f"HTTPException when trying to delete message ID {message_id} for user {player}: {e}")
            except Exception as e:
                self.bot.logger.error(
                    "An exception occurred when trying to delete " +
                    f"message ID {message_id} for user {player}: {e}"
                )
                traceback.print_exception(type(e), e, e.__traceback__)

    async def reset_button_vc_move(self, payload: VCResetPayload) -> None:
        for team in payload.teams:
            try:
                await self._move_team_to_lobby_vc(
                    payload.guild_id,
                    payload.lobby_vc_id,
                    team,
                    Reason.MATCH_FINALISED_LOBBY_MOVE
                )
            except discord.HTTPException:
                pass

    async def delete_vcs(self, payload: MatchFinalisedPayload) -> None:
        for team in payload.teams:
            try:
                await self._move_team_to_lobby_vc(
                    payload.guild_id,
                    payload.lobby_vc_id,
                    team,
                    Reason.MATCH_FINALISED_LOBBY_MOVE
                )
            except discord.HTTPException:
                pass

            # After moving everyone, THEN delete the VC
            await self.bot.get_channel(team.voice_channel_id).delete(reason=Reason.MATCH_FINALISED_DEL_TEMP)

    async def queue_match_cleanup(self, payload: MatchFinalisedPayload) -> None:
        await self.bot.queue_manager.delete_queue(
            payload.guild_id,
            payload.name,
            payload.owner_id,
        )
        await self.bot.match_manager.delete_match(
            payload.guild_id,
            payload.name,
        )

    async def delete_dms(self, payload: MatchFinalisedPayload) -> None:
        for team in payload.teams:
            await self._delete_dms(payload.guild_id, team.players)

    async def explicit_delete_dms(self, payload: DMDeletePayload) -> None:
        await self._delete_dms(payload.guild_id, payload.players)


async def setup(bot):
    await bot.add_cog(MonitoringCog(bot))
