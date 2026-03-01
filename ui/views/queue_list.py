from typing import List, Tuple

import discord

from ..urls import R6URL
from .paginator import *


class QueueListView(Paginator):
    def __init__(self, *, source_interaction: discord.Interaction, data, criteria: List[str], per_page: int = 3):
        super().__init__(
            source_interaction=source_interaction,
            data=data,
            per_page=per_page,
            timeout=None
        )

        # Type hints
        from queuemanager import QueueEntry
        self._data: List[Tuple[str, QueueEntry]] = data

        self.criteria = criteria

    def paginate_text_display(self) -> List[discord.ui.Item]:
        items = []
        index_base = self.per_page * self.current_page

        for index in range(index_base, index_base + self.per_page):
            try:
                name, entry = self._data[index]
                players = f"- Players: `{len(entry.players)}/{entry.max_players}`"
                if entry.players:
                    players += "\n" + "\n".join([
                        f"  - <@{_id}>" for _id in entry.players
                    ])
                items.append(discord.ui.TextDisplay(
                    "\n".join([
                        f"### {index + 1}. {name.title()} [{entry.type}]",
                        f"- Created On: `{entry.created_date}`",
                        f"- Owner: <@{entry.owner_id}>",
                        players,
                        f"- Locked: `{"Yes" if entry.locked else "No"}`",
                        f"- In Progress: `{"Yes" if entry.in_progress else "No"}`",
                    ])
                ))
                items.append(discord.ui.Separator())
            except IndexError:
                break
        return items

    def init_components(self) -> None:
        container = discord.ui.Container(
            # Header section, name type and page
            discord.ui.Section(
                discord.ui.TextDisplay(
                    content=f"## Queue List [Page {self.current_page + 1}/{self.max_pages}]",
                ),
                accessory=discord.ui.Thumbnail(R6URL.ICON)
            ),
            discord.ui.Separator(),

            # Actual part that displays the queue details
            *self.paginate_text_display(),

            # Separator is padded at the end in *text_displays
            discord.ui.TextDisplay(
                content=f"-# Matched criteria:  {"All Open Queues" if not self.criteria else " | ".join(self.criteria)}"
            ),
        )

        # Don't add navigation buttons unless they are needed
        if len(self._data) > self.per_page:
            if self.action_buttons is None:
                self.action_buttons = PaginatorButtonRow(view=self)
            self.action_buttons.init_components()
            container.add_item(self.action_buttons)

        # Add container to View
        self.add_item(container)
