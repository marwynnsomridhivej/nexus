import random
from typing import Coroutine, Dict, List, Tuple

import discord
from discord import app_commands
from discord.ext import commands

from canned import Canned
from event import *
from exceptions import *
from queuemanager import CaptSelect
from ui import *


class MatchCog(commands.GroupCog, name="match"):
    def __init__(self, bot):
        from bot import Bot
        self.bot: Bot = bot

    async def cog_load(self):
        _handlers: Dict[Coroutine, Event] = {
            self._init_match_data: Event.PREMATCH_MODAL_DONE,
            self._prematch_dm: Event.PREMATCH_DM_READY_SEND,
        }
        for coro, event in _handlers.items():
            self.bot.add_listener(coro, f"on_{event}")

        self.bot.logger.info("[MatchCog] Successfully loaded")

    async def _prematch_dm(self, payload: PrematchDMPayload) -> None:
        for user_id in payload.entry.players:
            user = self.bot.get_user(user_id)
            if user is None:
                continue
            message = await user.send(view=MatchStartDMView(
                guild=self.bot.get_guild(payload.guild_id),
                payload=payload,
            ))
            await self.bot.dm_manager.create(payload.guild_id, user_id, message.id)

    async def _init_match_data(self, payload: PrematchPayload) -> None:
        await self.bot.match_manager.create_match(payload=payload)

        match = await self.bot.match_manager.get_match(payload.guild_id, payload.match_name)

        # Create thread channel
        tc = self.bot.get_channel(payload.text_channel_id)
        thread_channel = await tc.create_thread(
            name=f"{payload.match_name} - {payload.entry.type}",
        )

        # Edit in place payload text channel ID to be thread channel now
        payload.switch_to_thread_channel(thread_channel.id)

        # Initialise R6View
        r6view = R6View(payload=payload, match=match, bot=self.bot)
        await r6view._set_order()
        r6view.init_components()

        # Send R6View to thread channel
        message = await thread_channel.send(view=r6view)
        self.bot.dispatch(Event.PREMATCH_DM_READY_SEND,
                          PrematchDMPayload.from_prematch_payload(payload, message))

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

        # Check if the guild has an active season
        try:
            await self.bot.stats_manager.ensure_season(guild_id=guild_id)
        except ValueError:
            return await interaction.response.send_message(Canned.ERR_SEASON_NO_EXISTS, ephemeral=True)

        # See if the person starting the match has any queues they can start from
        owned_queues = await self.bot.queue_manager.get_queues_owned_by(guild_id, owner_id)
        valid_owned_queues = {
            name: entry for name, entry in owned_queues.items()
            if len(entry.players) >= 2
            and not entry.in_progress
        }
        if not valid_owned_queues:
            return await interaction.response.send_message(Canned.ERR_MATCH_START, ephemeral=True)

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
            await interaction.followup.send(Canned.ERR_MATCH_IN_PROGRESS, ephemeral=True)

        # For type hints
        assert isinstance(prematch_modal.vc.component,
                          discord.ui.ChannelSelect)
        assert isinstance(prematch_modal.tc.component,
                          discord.ui.ChannelSelect)
        assert isinstance(prematch_modal.captain_select.component,
                          discord.ui.RadioGroup)
        assert isinstance(prematch_modal.manual_select.component,
                          discord.ui.UserSelect)

        vc = prematch_modal.vc.component.values[0]
        tc = prematch_modal.tc.component.values[0]
        mode = prematch_modal.captain_select.component.value

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

        # Confirmation message and event dispatch
        await interaction.followup.send(Canned.MATCH_DM_CONF, ephemeral=True)
        self.bot.dispatch(Event.PREMATCH_MODAL_DONE, payload)


async def setup(bot):
    await bot.add_cog(MatchCog(bot))
