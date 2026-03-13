import traceback
from typing import Dict, List

import discord

from canned import Canned
from exceptions import *
from queuemanager import *


class PreMatchModal(discord.ui.Modal):
    def __init__(self, bot, options: Dict[str, QueueEntry]):
        super().__init__(title="Match Configuration")
        self.is_valid: bool = True
        self.options = options

        from bot import Bot
        self.__bot: Bot = bot

        items = self._init_components()
        for item in items:
            self.add_item(item)

    def _init_components(self) -> List[discord.ui.Item]:
        self.queue = discord.ui.Label(
            text="Select Queue",
            description="For which queue would you like to start a match?",
            component=discord.ui.Select(
                options=[
                    discord.SelectOption(label=name, value=name) for name in self.options.keys()
                ],
                required=True,
            ),
        )
        self.vc = discord.ui.Label(
            text="Voice Channel",
            description="What voice channel should players connect to BEFORE team draft occurs?",
            component=discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.voice],
                required=True,
            ),
        )
        self.tc = discord.ui.Label(
            text="Text/Thread Channel",
            description="Which text channel should a thread be created in to house all messages related to this match?",
            component=discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.text],
                required=True,
            )
        )
        self.captain_select = discord.ui.Label(
            text="Captain Selection",
            description="How should captain selection occur?",
            component=discord.ui.RadioGroup(
                options=[
                    discord.RadioGroupOption(
                        label=CaptSelect.RATING.title(), value=CaptSelect.RATING),
                    discord.RadioGroupOption(
                        label=CaptSelect.RANDOM.title(), value=CaptSelect.RANDOM),
                    discord.RadioGroupOption(
                        label=CaptSelect.MANUAL.title(), value=CaptSelect.MANUAL),
                ],
                required=True,
            ),
        )
        self.manual_select = discord.ui.Label(
            text="Manual Selection",
            description=f"Select two captains if \"{CaptSelect.MANUAL.title()}\" was chosen as the captain selection method.",
            component=discord.ui.UserSelect(
                required=False,
                min_values=2,
                max_values=2,
            ),
        )
        return (self.queue, self.vc, self.tc, self.captain_select, self.manual_select)

    async def _ensure_perms(self, interaction: discord.Interaction) -> None:
        # Bot as member
        _member = interaction.guild.get_member(self.__bot.user.id)

        assert isinstance(self.vc.component, discord.ui.ChannelSelect)
        assert isinstance(self.tc.component, discord.ui.ChannelSelect)

        vc = await self.vc.component.values[0].fetch()
        vc_perms = vc.permissions_for(_member)
        assert vc_perms.move_members

        tc = await self.tc.component.values[0].fetch()
        tc_perms = tc.permissions_for(_member)
        assert tc_perms.send_messages
        assert tc_perms.add_reactions

    async def on_submit(self, interaction: discord.Interaction):
        # Ensure bot has correct permissions for specified channels
        await self._ensure_perms(interaction)

        # Ensure captain select values are OK
        assert isinstance(self.captain_select.component, discord.ui.RadioGroup)
        if self.captain_select.component.value == CaptSelect.MANUAL:
            assert isinstance(self.queue.component, discord.ui.Select)
            assert isinstance(self.manual_select.component,
                              discord.ui.UserSelect)

            if len(self.manual_select.component.values) != 2:
                raise InvalidCaptainManualSelect
            for user in self.manual_select.component.values:
                if user.bot:
                    raise UserIsBot(user)

                if not user.id in self.options[self.queue.component.values[0]].players:
                    raise InvalidUserSelected(user)

        await interaction.response.defer()
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        if isinstance(error, UserIsBot):
            msg = Canned.ERR_R6PRE_BOT_USER
        elif isinstance(error, InvalidUserSelected):
            msg = Canned.ERR_R6PRE_INVALID_USER
        elif isinstance(error, InvalidCaptainManualSelect):
            msg = Canned.ERR_R6PRE_INVALID_MANUAL
        else:
            msg = Canned.ERR_R6PRE_GEN
            self.__bot.logger.error(
                f"An exception occurred when trying to start match: {error}"
            )
            traceback.print_exception(type(error), error, error.__traceback__)

        await interaction.response.send_message(msg, ephemeral=True)
        self.is_valid = False
        self.stop()
