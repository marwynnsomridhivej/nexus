import random
import traceback
from typing import List, Tuple

import discord

from event import *
from matchmanager import R6_RANKED, MatchEntry, MatchTeam

from ..modals import *
from ..urls import R6URL

CANNED = {
    # fmt: off
    "owner":            "ERROR - Only the queue owner can execute this",
    "captain":          "ERROR - Only a team captain can execute this",

    "no_draftable":     "ERROR - There are no players available to draft",
    "draft_not_turn":   "ERROR - It is not your turn to draft players",

    "ban_not_turn":     "ERROR - It is not your turn to ban maps",

    "side":             "ERROR - Your team cannot select which side to start on",

    "finalised":        "ERROR - The match results have been finalised and cannot be modified",
    # fmt: on
}
INIT_DISABLED = [
    "Ban Map",
    "Side Select",
    "Designate MVP",
    "Report Results",
    "Reset",
]


class R6ViewButtons(discord.ui.ActionRow):
    def __init__(self, *, view: "R6View"):
        super().__init__()
        self._r6view = view

        self._set_button_default_state()

    def _increment_index(self, index: str) -> None:
        self._index[index] += 1
        self._index[index] %= 2

    async def _set_disabled(self, interaction: discord.Interaction, *, label: str, disabled: bool) -> None:
        button = None
        for child in self.children:
            if type(child) == discord.ui.Button and child.label == label:
                button = child
                break
        else:
            return

        if button.disabled != disabled:
            button.disabled = disabled
            await interaction.message.edit(view=self._r6view)

    def _set_button_default_state(self) -> None:
        """Sets all buttons to their default fresh state.

        Note: This does NOT automatically update the view.
        """
        for item in self.children:
            if type(item) == discord.ui.Button and item.label in INIT_DISABLED:
                item.disabled = True
            else:
                item.disabled = False
        self._index = {
            "draft": 0,
            "ban": 0,
        }

    def _is_captain(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in self._r6view._match.captains

    def _is_queue_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self._r6view._payload.entry.owner_id

    async def reset_to_default(self, interaction: discord.Interaction) -> None:
        await self._r6view._bot.match_manager.reset_draft(interaction.guild_id, self._r6view._payload.match_name)
        await self._r6view._update_match()
        await interaction.response.send_message(
            content="Player draft, map bans, and starting side selection have been reset",
            delete_after=10.0
        )

        # Dispatch unlisten events and then move everyone back
        self._r6view._dispatch_stop_team_vc_move()
        self._r6view._dispatch_reset_button_pressed()

        # Set view buttons to default state
        self._set_button_default_state()
        await interaction.message.edit(view=self._r6view)

    @discord.ui.button(label="Draft Player", style=discord.ButtonStyle.green)
    async def _draft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            return await interaction.response.send_message(CANNED["captain"], ephemeral=True)

        # Check to ensure the player interacting with this button is the one that should be drafting
        if self._r6view._draft_order[self._index["draft"]].id != interaction.user.id:
            return await interaction.response.send_message(CANNED["draft_not_turn"], ephemeral=True)

        draft_modal = R6DraftModal(view=self._r6view)
        await interaction.response.send_modal(draft_modal)
        await draft_modal.wait()

        # Increment draft index
        self._increment_index("draft")

        # Allow the RESET button to be pressed
        await self._set_disabled(interaction, label="Reset", disabled=False)

        # If everyone is drafted, make this button disabled and enable BAN MAP
        if self._r6view.finished_draft:
            button.disabled = True
            await self._r6view._create_team_vcs()
            await self._r6view._dispatch_team_vc_move()
            await self._set_disabled(interaction, label="Ban Map", disabled=False)

        # Update the text on the R6View
        await self._r6view._update_txt_content(interaction)

    @discord.ui.button(label="Ban Map", style=discord.ButtonStyle.red)
    async def _ban_map_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            return await interaction.response.send_message(CANNED["captain"], ephemeral=True)

        # Draft order already initialised, can jump right in
        if self._r6view._op_draft_order[self._index["ban"]].id != interaction.user.id:
            return await interaction.response.send_message(CANNED["ban_not_turn"], ephemeral=True)

        map_ban_modal = R6MapBanModal(view=self._r6view)
        await interaction.response.send_modal(map_ban_modal)
        await map_ban_modal.wait()

        # Increment ban index
        self._increment_index("ban")

        # Reset button SHOULD be allowed from draft already, but do again anyway
        await self._set_disabled(interaction, label="Reset", disabled=False)

        # If all maps EXCEPT one are banned, make this button disabled and enable SIDE SELECT
        if self._r6view.finished_map_bans:
            button.disabled = True
            await self._set_disabled(interaction, label="Side Select", disabled=False)
            await self._r6view._bot.get_channel(self._r6view._payload.text_channel_id).send(
                f"The selected map is: **{self._r6view._match.map.replace("_", "").title()}**",
                delete_after=10.0
            )

        # Update the text on the R6View
        await self._r6view._update_txt_content(interaction)

    @discord.ui.button(label="Side Select", style=discord.ButtonStyle.blurple)
    async def _side_select_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            return await interaction.response.send_message(CANNED["captain"], ephemeral=True)

        if self._r6view._op_draft_order[self._index["draft"]].id != interaction.user.id:
            return await interaction.response.send_message(CANNED["side"], ephemeral=True)

        side_modal = R6SideModal(view=self._r6view)
        await interaction.response.send_modal(side_modal)
        await side_modal.wait()

        if self._r6view.finished_side_select:
            button.disabled = True
            await self._set_disabled(interaction, label="Designate MVP", disabled=False)
            await self._set_disabled(interaction, label="Report Results", disabled=False)

        # Update the text on the R6View
        await self._r6view._update_txt_content(interaction)

    @discord.ui.button(label="Designate MVP", style=discord.ButtonStyle.blurple)
    async def _designate_mvp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            return await interaction.response.send_message(CANNED["captain"], ephemeral=True)

        mvp_modal = R6MVPModal(
            view=self._r6view,
            captain_id=interaction.user.id,
        )
        await interaction.response.send_modal(mvp_modal)
        await mvp_modal.wait()

        # Different than others, since we want to disable this button as opposed to enable another
        if self._r6view._match.mvps_set:
            await self._set_disabled(interaction, label="Designate MVP", disabled=True)

        # If this action finalises the match results (win + mvp set for both teams), disable view
        if self._r6view._check_finalised():
            await self._r6view._disable_reset_button(interaction)

            # Update the text on the R6View
        await self._r6view._update_txt_content(interaction)

    @discord.ui.button(label="Report Results", style=discord.ButtonStyle.grey)
    async def _report_results_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_queue_owner(interaction):
            return await interaction.response.send_message(CANNED["owner"], ephemeral=True)

        result_modal = R6ResultModal(view=self._r6view)
        await interaction.response.send_modal(result_modal)
        await result_modal.wait()

        if self._r6view._match.wins_set:
            # Similar to Designate MVP, disable this button once winner/loser is set
            await self._set_disabled(interaction, label="Report Results", disabled=True)

        # If this action finalises the match results (win + mvp set for both teams), disable view
        if self._r6view._check_finalised():
            await self._r6view._disable_reset_button(interaction)

            # Update the text on the R6View
        await self._r6view._update_txt_content(interaction)


class R6ViewResetButton(discord.ui.ActionRow):
    def __init__(self, *, view, other_row: "R6ViewButtons"):
        super().__init__()

        self._r6view: R6View = view
        self._other_row = other_row

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.grey)
    async def _reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._other_row._is_queue_owner(interaction):
            return await interaction.response.send_message(CANNED["owner"], ephemeral=True)

        if self._other_row._r6view._match.finalised:
            button.disabled = True
            await interaction.message.edit(view=self._other_row._r6view)
            return await interaction.response.send_message(CANNED["finalised"], ephemeral=True)

        await self._other_row.reset_to_default(interaction)
        await self._r6view._update_txt_content(interaction)


class R6View(discord.ui.LayoutView):
    def __init__(self, *, payload: PrematchPayload, match: MatchEntry, bot):
        super().__init__(timeout=None)
        self._payload = payload
        self._match = match

        from bot import Bot
        self._bot: Bot = bot

    def init_components(self) -> None:
        self.map_pool = sorted(random.sample(R6_RANKED, k=7))

        self.about_text = discord.ui.TextDisplay(self._get_txt_content())
        self.thumbnail = discord.ui.Thumbnail(media=R6URL.ICON)
        self.section = discord.ui.Section(
            self.about_text, accessory=self.thumbnail)

        self.view_buttons = R6ViewButtons(view=self)
        self.r6_view_reset_button = R6ViewResetButton(
            view=self,
            other_row=self.view_buttons)
        container = discord.ui.Container(
            self.section, self.view_buttons, self.r6_view_reset_button, accent_color=discord.Color.blurple())
        self.add_item(container)

    async def _set_order(self) -> None:
        # For:
        #   Player Draft    --> LOWEST points goes first
        #   Map Ban         --> HIGHEST points bans first
        #   Starting Side   --> LOWEST points goes first (use draft[0])
        self._draft_order = sorted([
            await self._bot.stats_manager.get_or_create_player(
                guild_id=self._payload.guild_id,
                user_id=_id,
            ) for _id in self._match.captains
        ], key=lambda p: p.points)
        self._op_draft_order = [self._draft_order[1], self._draft_order[0]]

    def _get_draftable(self) -> List[Tuple[str, str]]:
        return [
            (self._bot.get_guild(
                self._payload.guild_id
            ).get_member(_id).display_name, str(_id))

            for _id in self._payload.entry.players if
            _id not in self._match.team_a.players and
            _id not in self._match.team_b.players
        ]

    def _get_team_players_txt(self, team: MatchTeam) -> List[int]:
        txt = f"### Team {team.name}"
        txt += " (Win)" if team.win is True else " (Lose)" if team.win is False else ""
        txt += "\n" + "\n".join([
            # - @Player *(captain?)* *(mvp?)*
            f"- <@{_id}>{" *(captain)*" if _id == team.captain_id else ""}{" *(mvp)*" if team.mvp_id is not None and _id == team.mvp_id else ""}" for _id in team.players
        ])
        return txt

    def _get_txt_content(self) -> str:
        items = []

        # Always put title
        title = f"## {self._payload.match_name.upper()} [{self._match.type.upper()}]"
        items.append(title)

        # Always put team roster
        team_draft = "\n".join([
            self._get_team_players_txt(self._match.team_a),
            self._get_team_players_txt(self._match.team_b),
        ])
        items.append(team_draft)

        # Show draft order if not done
        if not self.finished_draft:
            draft_order = "\n".join([
                "### Player Draft Order",
                f"1. <@{self._draft_order[0].id}>",
                f"2. <@{self._draft_order[1].id}>",
            ])
            items.append(draft_order)

        # Show map ban order if not done, otherwise show selected map
        if not self.finished_map_bans:
            ban_order = "\n".join([
                "### Map Ban Order",
                f"1. <@{self._op_draft_order[0].id}>",
                f"2. <@{self._op_draft_order[1].id}>",
            ])
            pool = "### Map Pool\n" + "\n".join([
                f"- {"~~" if r6map in self._match.banned_maps else ""}{r6map.replace("_", " ").title()}{"~~" if r6map in self._match.banned_maps else ""}" for r6map in self.map_pool
            ])
            items.append(ban_order)
            items.append(pool)
        else:
            selected_map = "### Selected Map\n" + \
                f"{self._match.map.replace("_", " ").title()}"
            items.append(selected_map)

        # Show who gets to select the starting side if not done, otherwise show side assignments
        if not self.finished_side_select:
            side_select = "\n".join([
                "### Starting Side Selection",
                f"- Performed by: <@{self._op_draft_order[0].id}>",
            ])
            items.append(side_select)
        else:
            starting_sides = "\n".join([
                "### Starting Sides",
                f"Team A: {self._match.team_a.starting_side.title()}s",
                f"Team B: {self._match.team_b.starting_side.title()}s",
            ])
            items.append(starting_sides)

        # Always put disclaimer
        disclaimer = "\n*Although everyone can click the buttons below, only " + \
            "team captains and the queue owner will be able to interact with them.*"
        items.append(disclaimer)

        return "\n".join(items)

    async def _update_txt_content(self, interaction: discord.Interaction) -> str:
        self.about_text.content = self._get_txt_content()
        await interaction.message.edit(view=self)

    async def _create_team_vcs(self) -> None:
        parent_vc = self._bot.get_channel(
            self._payload.voice_channel_id)
        for offset, team in enumerate(self.teams):
            # Create and set team voice channel if it isn't already set
            # This should not be redone after a reset
            if team.voice_channel_id is None:
                coro = parent_vc.category.create_voice_channel\
                    if isinstance(parent_vc.category, discord.CategoryChannel)\
                    else self._bot.get_guild(self._payload.guild_id).create_voice_channel
                vc = await coro(
                    name=f"{self._payload.match_name} - Team {team.name}",
                    reason=f"Automated team voice channel creation for match {self._payload.match_name}",
                    position=parent_vc.position + offset,
                )
                await self._bot.match_manager.set_team_vc(
                    self._payload.guild_id,
                    self._payload.match_name,
                    team.captain_id,
                    vc.id
                )
                await self._update_match()

    async def _dispatch_team_vc_move(self) -> None:
        for team in self.teams:
            # Try to move individual players first
            team_vc = self._bot.get_channel(team.voice_channel_id)
            for player_id in team.players:
                try:
                    await self._bot\
                        .get_guild(self._payload.guild_id)\
                        .get_member(player_id)\
                        .move_to(team_vc, reason=Reason.TEAM_VC)
                except discord.HTTPException:
                    pass
                except Exception as e:
                    traceback.print_exception(type(e), e, e.__traceback__)

            # Then create listeners to auto route players to their team VC if they are disconnected
            self._bot.dispatch(Event.VC_LISTENER_ADD, VCPayload.create_add(
                self._match.voice_channel_id,
                team.voice_channel_id,
                team.players,
            ))

    def _dispatch_stop_team_vc_move(self) -> None:
        self._bot.dispatch(Event.VC_LISTENER_REMOVE, VCPayload.create_remove(
            self._match.voice_channel_id,
            self._match.team_a.players + self._match.team_b.players,
        ))

    def _dispatch_reset_button_pressed(self) -> None:
        self._bot.dispatch(Event.RESET_BUTTON_PRESSED, VCResetPayload.create(
            self._payload.guild_id,
            self._match.voice_channel_id,
            [self._match.team_a, self._match.team_b],
        ))

    async def _update_match(self) -> MatchEntry:
        self._match = await self._bot.match_manager.get_match(self._payload.guild_id, self._payload.match_name)

    def _check_finalised(self) -> bool:
        if self._match.finalised:
            # Stop listening to events on this View
            self.stop()

            # Remove all vc redirects
            self._dispatch_stop_team_vc_move()

            # Dispatch match finalised to teardown vcs
            self._bot.dispatch(Event.MATCH_FINALISED, MatchFinalisedPayload.create(
                self._payload.guild_id,
                self._match,
            ))
            return True
        return False

    async def _disable_reset_button(self, interaction: discord.Interaction) -> None:
        for child in self.r6_view_reset_button.children:
            if type(child) == discord.ui.Button:
                child.disabled = True
        await interaction.message.edit(view=self)

    @property
    def teams(self) -> List[MatchTeam]:
        return [self._match.team_a, self._match.team_b]

    @property
    def finished_draft(self) -> bool:
        return not bool(self._get_draftable())

    @property
    def finished_map_bans(self) -> bool:
        return self._match.has_map

    @property
    def finished_side_select(self) -> bool:
        return self._match.sides_selected
