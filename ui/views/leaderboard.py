from datetime import datetime
from typing import List, Tuple

import discord

from .paginator import Paginator, PaginatorButtonRow


class LeaderboardView(Paginator):
    def __init__(self, *, source_interaction, rankings):
        super().__init__(
            source_interaction=source_interaction,
            data=rankings,
            per_page=8,
        )

        from statsmanager import StatsPlayer
        self._data: List[Tuple[int, StatsPlayer]] = rankings

        self.created_time = f"<t:{int(datetime.now().timestamp())}:f>"

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
