import traceback
from typing import List

import discord

from matchmanager import MatchTeam


class R6ResultModal(discord.ui.Modal):
    def __init__(self, *, view):
        super().__init__(title="Report Results")

        from ..views import R6View
        self._r6view: R6View = view

        for item in self._init_components():
            self.add_item(item)

    def _init_components(self) -> List[discord.ui.Item]:
        self.result = discord.ui.Label(
            text="Match Results",
            description="Select the winning team",
            component=discord.ui.Select(
                options=[
                    discord.SelectOption(
                        label=f"Team {self._get_captain_name(team)}",
                        value=team.captain_id
                    ) for team in self._r6view.teams
                ],
                required=True,
            )
        )
        return [self.result]

    def _get_captain_name(self, team: MatchTeam) -> str:
        return self._r6view._bot\
            .get_guild(self._r6view._payload.guild_id)\
            .get_member(team.captain_id).display_name

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.result.component, discord.ui.Select)

        captain_id = int(self.result.component.values[0])
        await self._r6view._bot.match_manager.set_winning_team(
            interaction.guild_id,
            self._r6view._payload.match_name,
            captain_id,
        )

        # Update local MatchEntry instance attached to R6View
        await self._r6view._update_match()

        winners = f"The winner of **{self._r6view._payload.match_name}** is Team {self._r6view._match.winning_team.name}"
        await interaction.response.send_message(content=winners)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        msg = "An error has occurred. Unable to report match results."
        traceback.print_exception(type(error), error, error.__traceback__)
        await interaction.response.send_message(msg)
