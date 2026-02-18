from typing import List

import discord

from ..views import R6View


class R6DraftModal(discord.ui.Modal):
    def __init__(self, *, view: R6View):
        super().__init__()
        self.__view = view

    def _get_draftable_ids(self) -> List[int]:
        return [
            _id for _id in self.__view._payload.entry.players if
            _id not in self.__view._match.team_a.players and
            _id not in self.__view._match.team_b.players
        ]
