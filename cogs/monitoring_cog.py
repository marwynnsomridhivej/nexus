from typing import Coroutine, Dict

import discord
from discord.ext import commands

from event import *
from matchmanager import MatchTeam


class MonitoringCog(commands.Cog):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot
        self.__data = {}

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self._listen: "voice_state_update",
            self.listen_vc: Event.VC_LISTENER_ADD,
            self.unlisten_vc: Event.VC_LISTENER_REMOVE,
            self.reset_button_vc_move: Event.RESET_BUTTON_PRESSED,
            self.queue_match_cleanup: Event.MATCH_FINALISED,
            self.delete_vcs: Event.MATCH_FINALISED,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        print("[MonitoringCog] Successfully loaded")

    async def _util_move_back_to_lobby(self, guild_id: int, lobby_vc_id: int, team: MatchTeam, reason: Reason) -> None:
        lobby_vc_channel = self.bot.get_channel(lobby_vc_id)

        # Try to move all the players in the team back to the "lobby VC"
        for player_id in team.players:
            member = self.bot\
                .get_guild(guild_id)\
                .get_member(player_id)
            if not isinstance(member, discord.Member):
                continue
            await member.move_to(lobby_vc_channel, reason=reason)

    async def _listen(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        # Ensure the new channel exists
        if after.channel is None:
            return

        # Ensure the channel is one of the ones we are already listening to
        if self.__data.get(after.channel.id) is None:
            return

        move_to_id = self.__data[after.channel.id][member.id]
        if move_to_id is not None:
            await member.move_to(self.bot.get_channel(move_to_id), reason=Reason.TEAM_VC)

    def _get_or_create(self, listen_id: int) -> dict:
        if self.__data.get(listen_id) is None:
            self.__data[listen_id] = {}
        return self.__data[listen_id]

    async def listen_vc(self, payload: VCPayload) -> None:
        # Ensure payload is for adding a listener
        assert payload.stop is False

        data = self._get_or_create(payload.vc_listen_id)
        for _id in payload.player_ids:
            data[_id] = payload.vc_dest_id

    async def unlisten_vc(self, payload: VCPayload) -> None:
        # Ensure payload is for removing a listener
        assert payload.stop is True

        data = self._get_or_create(payload.vc_listen_id)
        for _id in payload.player_ids:
            if data.get(_id) is not None:
                del data[_id]

        # Delete the listen ID entry if nobody is in there
        if not data:
            del self.__data[payload.vc_listen_id]

    async def reset_button_vc_move(self, payload: VCResetPayload) -> None:
        for team in payload.teams:
            try:
                await self._util_move_back_to_lobby(
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
                await self._util_move_back_to_lobby(
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


async def setup(bot):
    await bot.add_cog(MonitoringCog(bot))
