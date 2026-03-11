from typing import List

import discord

from statsmanager import StatsPlayer, StatsSeason

from ..urls import R6URL


class SeasonEndDMView(discord.ui.LayoutView):
    def __init__(self, *, guild: discord.Guild, season: StatsSeason, player: StatsPlayer, rank: int):
        super().__init__(timeout=None)

        self._guild = guild
        self._season = season
        self._player = player
        self._rank = rank

        self.init_components()

    @property
    def text_display(self) -> List[discord.ui.Item]:
        items = []

        # Header
        header = discord.ui.TextDisplay("\n".join([
            f"## End of Season Summary - {self._season.name.title()}",
            f"The administrators for *{self._guild.name}* have ended the " +
            "current season. Here is a recap on your performance and server rank.",
        ]))
        items.append(header)
        items.append(discord.ui.Separator())

        # Individual Stats
        stats = discord.ui.TextDisplay("\n".join([
            f"### Individual Stats",
            f"- Server rank: `{self._rank}`/`{self._season.player_count}`",
            f"- Matches Played: `{self._player.matches_played}`",
            f"- Points: `{self._player.points}` `({self._player.max_points} peak)`",
            f"- Wins: `{self._player.wins}`",
            f"- Losses: `{self._player.losses}`",
            f"- Winrate (W/L ratio): `{self._player.wl_ratio * 100}`",
            f"- Times MVP: `{self._player.times_mvp}`",
        ]))
        items.append(stats)
        items.append(discord.ui.Separator())

        # Ranking footer disclaimer
        disclaimer = discord.ui.TextDisplay(
            "-# Note that multiple people can have the same rank if they have the " +
            "same amount of points",
        )
        items.append(disclaimer)

        return items

    def init_components(self) -> None:
        container = discord.ui.Container(
            discord.ui.Section(
                *self.text_display[:1],
                accessory=discord.ui.Thumbnail(
                    self._guild.icon.url if self._guild.icon is not None else R6URL.ICON
                )
            ),
            *self.text_display[1:],
            accent_color=discord.Color.blurple(),
        )
        self.add_item(container)
