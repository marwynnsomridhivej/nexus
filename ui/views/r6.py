import discord

from matchmanager import MatchEntry, PrematchPayload

from ..urls import R6URL


class R6ViewButtons(discord.ui.ActionRow):
    def __init__(self, *, view: "R6View"):
        super().__init__()
        self.__view = view
        self._canned = {
            "owner": "ERROR - Only the queue owner can execute this",
            "captain": "ERROR - Only a team captain can execute this",
        }

    def _is_captain(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in self.__view._match.captains

    def _is_queue_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.__view._payload.entry.owner_id

    @discord.ui.button(label="Draft", style=discord.ButtonStyle.green)
    async def _draft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            msg = self._canned["captain"]
        else:
            msg = "Draft"

        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="Ban Map", style=discord.ButtonStyle.red)
    async def _ban_map_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            msg = self._canned["captain"]
        else:
            msg = "Ban Map"

        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="Designate MVP", style=discord.ButtonStyle.blurple)
    async def _designate_mvp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_captain(interaction):
            msg = self._canned["captain"]
        else:
            msg = "Designate MVP"

        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="Report Results", style=discord.ButtonStyle.blurple)
    async def _report_results(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_queue_owner(interaction):
            msg = self._canned["owner"]
        else:
            msg = "Report Results"

        await interaction.response.send_message(msg, ephemeral=True)


class R6View(discord.ui.LayoutView):
    def __init__(self, *, payload: PrematchPayload, match: MatchEntry):
        super().__init__(timeout=None)
        self._payload = payload
        self._match = match

        self.about_text = discord.ui.TextDisplay(self._get_txt_content())
        self.thumbnail = discord.ui.Thumbnail(media=R6URL.ICON)
        self.section = discord.ui.Section(
            self.about_text, accessory=self.thumbnail)
        container = discord.ui.Container(
            self.section, R6ViewButtons(view=self), accent_color=discord.Color.blurple())
        self.add_item(container)

    def _get_txt_content(self) -> str:
        title = f"## {self._payload.match_name.upper()} [{self._match.type.upper()}]"
        content = "\n".join([
            "**Team Captains**",
            f"- Team A: <@{self._match.team_a.captain_id}>",
            f"- Team B: <@{self._match.team_b.captain_id}>",
        ])
        disclaimer = "\n*Although everyone can click the buttons below, only" + \
            "team captains and the queue owner will be able to interact with them.*"

        return "\n".join([title, content, disclaimer])
