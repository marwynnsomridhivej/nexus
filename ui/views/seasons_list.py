from typing import List

import discord

from .paginator import Paginator, PaginatorButtonRow


class SeasonsListView(Paginator):
    def __init__(self, *, source_interaction: discord.Interaction, seasons):
        super().__init__(
            source_interaction=source_interaction,
            data=seasons,
            per_page=5,
        )

        from statsmanager import StatsSeason
        self._seasons: List[StatsSeason] = seasons

    def paginate_text_display(self) -> List[discord.ui.Item]:
        items = []
        index_base = self.per_page * self.current_page

        for index in range(index_base, index_base + self.per_page):
            try:
                season = self._seasons[index]
                items.append(discord.ui.TextDisplay(
                    "\n".join([
                        f"### {season.name.title()}{" (Current)" if season.is_current else ""}",
                        f"> - Started: <t:{season.start_timestamp}:f>",
                        f"> - Ended: {f"<t:{season.end_timestamp}:f>" if season.end_timestamp is not None else "`ONGOING`"}",
                        f"> - Ranked Players: `{season.player_count}`",
                        f"> - Matches Played: `{season.match_count}`",
                    ])
                ))
                items.append(discord.ui.Separator())
            except IndexError:
                items.pop()
                break
        return items

    def init_components(self) -> None:
        container = discord.ui.Container(
            discord.ui.TextDisplay("## All Seasons"),
            *self.paginate_text_display(),
            accent_color=discord.Color.blurple(),
        )

        if len(self._data) > self.per_page:
            if self.action_buttons is None:
                self.action_buttons = PaginatorButtonRow(view=self)
            self.action_buttons.init_components()
            container.add_item(self.action_buttons)

        self.add_item(container)
