import traceback
from typing import List

import discord

from matchmanager import R6Side


class R6SideModal(discord.ui.Modal):
    def __init__(self, *, view):
        super().__init__(title="Starting Side Selection")

        from ..views import R6View
        self._r6view: R6View = view

        for item in self._init_components():
            self.add_item(item)

    def _init_components(self) -> List[discord.ui.Item]:
        self.side_select = discord.ui.Label(
            text="Starting Side Selection",
            description="Select whether your team would like to attack or defend first",
            component=discord.ui.Select(
                options=[
                    discord.SelectOption(
                        label=side.title(),
                        value=side.value
                    ) for side in [R6Side.ATTACKER, R6Side.DEFENDER]
                ],
                required=True,
            ),
        )
        return [self.side_select]

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.side_select.component, discord.ui.Select)

        captain_id = interaction.user.id
        choice = self.side_select.component.values[0]

        # Set starting side according to selection
        await self._r6view._bot.match_manager.select_starting_side(
            interaction.guild_id,
            self._r6view._payload.match_name,
            captain_id,
            R6Side(choice)
        )

        # Update local MatchEntry instance attached to R6View
        await self._r6view._update_match()

        await interaction.response.send_message(
            content=f"Captain <@{captain_id}>'s team will start as **{choice.lower()}s**.",
            delete_after=10.0
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        msg = "An error has occurred. Unable to select starting side."
        self._r6view._bot.logger.error(
            f"An exception occurred when trying to select starting side: {error}"
        )
        traceback.print_exception(type(error), error, error.__traceback__)
        await interaction.response.send_message(msg)
