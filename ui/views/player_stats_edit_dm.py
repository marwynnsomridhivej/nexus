from typing import List

import discord

from statsmanager import StatsPlayer

from ..urls import R6URL


class PlayerStatsEditDMView(discord.ui.LayoutView):
    def __init__(self, *, user: discord.User, guild: discord.Guild, previous: StatsPlayer, new: StatsPlayer):
        super().__init__(timeout=None)

        self.user = user
        self.guild = guild
        self.previous = previous
        self.new = new

        self.init_components()

    @property
    def text_display(self) -> List[discord.ui.Item]:
        items = []

        # Header
        header = discord.ui.TextDisplay("\n".join([
            "## Alert - Stats Edited",
            f"An administrator for the server `{self.guild.name}` edited your stats for the current active season.",
        ]))
        items.append(header)

        # Body
        body = discord.ui.TextDisplay("\n".join([
            "### Details",
            f"- Wins: `{self.previous.wins}` ⟶ `{self.new.wins}`",
            f"- Losses: `{self.previous.losses}` ⟶ `{self.new.losses}`",
            f"- Points: `{self.previous.points}` ⟶ `{self.new.points}`",
            f"- Peak Points: `{self.previous.max_points}` ⟶ `{self.new.max_points}`",
            f"- Times MVP: `{self.previous.times_mvp}` ⟶ `{self.new.times_mvp}`",
            "### Disclaimer",
            "Although stat edits may be used as a disciplinary measure, having your stats reset is not always " +
            "an indicator that disciplinary action has been taken against you.",
        ]))
        items.append(body)

        return items

    def init_components(self) -> None:
        container = discord.ui.Container(
            discord.ui.Section(
                self.text_display[0],
                accessory=discord.ui.Thumbnail(
                    self.guild.icon.url if self.guild.icon is not None else R6URL.ICON
                )
            ),
            self.text_display[1],
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                "-# If you believe this edit was performed in error, please contact server administrators"
            ),
            accent_color=discord.Color.blurple(),
        )
        self.add_item(container)
