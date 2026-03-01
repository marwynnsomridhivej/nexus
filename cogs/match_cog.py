import random
from typing import Coroutine, Dict, List, Tuple

import discord
from discord import app_commands
from discord.ext import commands

from event import Event, PrematchPayload
from exceptions import *
from queuemanager import CaptSelect
from ui import *


class MatchCog(commands.GroupCog, name="match"):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self._prematch_dm: Event.PREMATCH_MODAL_DONE,
            self._init_match_data: Event.PREMATCH_MODAL_DONE,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        print("[MatchCog] Successfully loaded")

    async def _prematch_dm(self, payload: PrematchPayload) -> None:
        msg = f"""A match you are queued for is starting: **{payload.match_name} - [{payload.entry.type}]**

The following will happen BEFORE you get into the custom:
1. Join the voice channel <#{payload.voice_channel_id}>
2. Team captains have been assigned: {" ".join([f"<@{user_id}>" for user_id in payload.captains])}
3. Players are drafted by team captains
    - *The lowest rated captain will get first pick, and picks alternate until no players remain*
4. Teams will be automatically split into isolated voice channels based on draft
5. Maps are banned until one is left
    - *The highest rated captain will get first ban, and bans alternate until one map remains*
6. Players join the lobby ingame and the game starts
    - *Lobby will be set up by any player in accordance to draft and map bans*
"""
        # TODO: Craft a message to be sent to captains once post-match flow is established
        for user_id in payload.entry.players:
            await self.bot.get_user(user_id).send(msg, delete_after=60)

    async def _init_match_data(self, payload: PrematchPayload) -> None:
        await self.bot.match_manager.create_match(payload=payload)

        match = await self.bot.match_manager.get_match(payload.guild_id, payload.match_name)
        r6view = R6View(payload=payload, match=match, bot=self.bot)

        # Need to initialise these outside of the R6View.__init__, since R6View._set_order() is async
        await r6view._set_order()
        r6view.init_components()

        tc = self.bot.get_channel(payload.text_channel_id)
        await tc.send(view=r6view)

    async def _select_captains(self, *, guild_id: int, players: List[int], mode: CaptSelect) -> Tuple[int, int]:
        match mode:
            case CaptSelect.RANDOM:
                return tuple(random.sample(players, 2))
            case CaptSelect.RATING:
                captains = sorted([
                    await self.bot.stats_manager.get_or_create_player(
                        guild_id=guild_id,
                        user_id=_id
                    ) for _id in players
                ], key=lambda p: p.points, reverse=True)
                return (captains[0].id, captains[1].id)
            case _:
                raise ValueError(mode)

    @app_commands.command(name="start", description="Enter pre-match configuration details")
    async def _start_match(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        owner_id = interaction.user.id
        owned_queues = await self.bot.queue_manager.get_queues_owned_by(guild_id, owner_id)
        valid_owned_queues = {
            name: entry for name, entry in owned_queues.items()
            if len(entry.players) >= 2
            and not entry.in_progress
        }
        if not valid_owned_queues:
            await interaction.response.send_message("Unable to start a match, as you are not the owner of any startable queues.")
            return

        prematch_modal = PreMatchModal(self.bot, valid_owned_queues)
        await interaction.response.send_modal(prematch_modal)

        # Ensure we don't access any attributes until user has submitted
        await prematch_modal.wait()

        # Don't do anything if we get an invalid answer or the modal errorred out
        if not prematch_modal.is_valid:
            return

        # Check if our entry can be started
        assert isinstance(prematch_modal.queue.component, discord.ui.Select)
        name: str = prematch_modal.queue.component.values[0]
        try:
            entry = await self.bot.queue_manager.start_match(guild_id, owner_id, name)
        except QueueProgressStateError:
            await interaction.followup.send(content="This match is already in progress")

        # For type hints
        assert isinstance(prematch_modal.vc.component,
                          discord.ui.ChannelSelect)
        assert isinstance(prematch_modal.tc.component,
                          discord.ui.ChannelSelect)
        assert isinstance(prematch_modal.captain_select.component,
                          discord.ui.Select)
        assert isinstance(prematch_modal.manual_select.component,
                          discord.ui.UserSelect)

        vc = prematch_modal.vc.component.values[0]
        tc = prematch_modal.tc.component.values[0]
        mode = prematch_modal.captain_select.component.values[0]

        # Craft payload to be dispatched on event
        if mode == CaptSelect.MANUAL:
            captains = tuple(
                userlike.id for userlike in prematch_modal.manual_select.component.values
            )
        else:
            captains = await self._select_captains(
                guild_id=guild_id,
                players=entry.players,
                mode=mode
            )
        payload = PrematchPayload.parse({
            "guild_id": guild_id,
            "match_name": name,
            "voice_channel_id": vc.id,
            "text_channel_id": tc.id,
            "captains": captains,
            "entry": entry,
        })

        # Dispatch and confirm
        self.bot.dispatch(Event.PREMATCH_MODAL_DONE, payload)
        await interaction.followup.send(content="Players will receive a match start notification in their DM shortly", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MatchCog(bot))
