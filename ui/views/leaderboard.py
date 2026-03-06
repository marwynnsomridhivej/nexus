from datetime import datetime
from typing import List, Tuple

import discord

from ..urls import R6URL
from .paginator import Paginator, PaginatorButtonRow


class LeaderboardView(Paginator):
    def __init__(self, *, source_interaction, data):
        super().__init__(
            source_interaction=source_interaction,
            data=data,
            per_page=8,
        )

        from statsmanager import StatsPlayer
        previous_points = None
        previous_rank = None
        data = []
        for rank, player in enumerate(self._data, 1):
            assert isinstance(player, StatsPlayer)

            # Initialise the previous point count if not set
            if previous_points is None:
                previous_points = player.points

            # Initialise the previous rank if not set
            if previous_rank is None:
                previous_rank = rank

            # Check if previous points is the same. If so, keep the previous rank as number
            if player.points == previous_points:
                data.append((previous_rank, player))
                continue

            # Otherwise, append the true rank and player and set previous points/rank to current player stats
            data.append((rank, player))
            previous_points = player.points
            previous_rank = rank
        self._data: List[Tuple[int, StatsPlayer]] = data

        self.created_time = datetime.now().strftime(r"%d/%m/%Y, %H:%M:%S")

    def paginate_text_display(self) -> List[discord.ui.Item]:
        items = []
        index_base = self.per_page * self.current_page

        for index in range(index_base, index_base + self.per_page):
            try:
                rank, player = self._data[index]
                items.append(discord.ui.TextDisplay(
                    "\n".join([
                        f"### {rank}. <@{player.id}>",
                        f"> - `{player.points}`pts (`{player.max_points}` peak)",
                        f"> - `{player.matches_played}` Match{"es" if player.matches_played != 1 else ""} Played",
                        f"> - `{player.wins}`W/`{player.losses}`L (`{player.wl_ratio * 100}%` WL)",
                        f"> - `{player.times_mvp}` time{"s" if player.times_mvp != 1 else ""} MVP",
                    ])
                ))
            except IndexError:
                break
        return items

    def init_components(self) -> None:
        container = discord.ui.Container(
            # Header, name type and page
            discord.ui.TextDisplay(
                f"## Leaderboard [Page {self.current_page + 1}/{self.max_pages}]"),

            # Actual part that displays leaderboard
            *self.paginate_text_display(),

            # Separator is padded at the end in *text_displays
            discord.ui.TextDisplay(
                f"-# Statistics tabulated as of {self.created_time}"),

            # Accent color
            accent_color=discord.Color.blurple(),
        )

        # Don't add navigation buttons unless they are needed
        if len(self._data) > self.per_page:
            if self.action_buttons is None:
                self.action_buttons = PaginatorButtonRow(view=self)
            self.action_buttons.init_components()
            container.add_item(self.action_buttons)

        # Add container to View
        self.add_item(container)
