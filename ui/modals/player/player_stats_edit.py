import traceback

import discord

from canned import Canned
from statsmanager import StatsPlayer


class PlayerStatsEditModal(discord.ui.Modal):
    def __init__(self, *, bot, player: StatsPlayer):
        super().__init__(title="Edit Player Stats")

        from bot import Bot
        self.bot: Bot = bot
        self.player = player

        # All items that we will actually reference later for values
        self.wins: discord.ui.Label = None
        self.losses: discord.ui.Label = None
        self.points: discord.ui.Label = None
        self.max_points: discord.ui.Label = None
        self.times_mvp: discord.ui.Label = None

        self.init_components()
        self.apply_edits = False

    @property
    def new_stats(self) -> dict:
        return {
            "wins": int(self.wins.component.value),
            "losses": int(self.losses.component.value),
            "points": int(self.points.component.value),
            "max_points": int(self.max_points.component.value),
            "times_mvp": int(self.times_mvp.component.value),
        }

    def init_components(self) -> None:
        self.wins = discord.ui.Label(
            text="Wins",
            description=f"How many matches has this player won? (Current: {self.player.wins})",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                min_length=1,
                default=str(self.player.wins),
            ),
        )
        self.losses = discord.ui.Label(
            text="Losses",
            description=f"How many matches has this player lost? (Current: {self.player.losses})",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                min_length=1,
                default=str(self.player.losses),
            ),
        )
        self.points = discord.ui.Label(
            text="Points",
            description=f"How many points does this player have? (Current: {self.player.points})",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                min_length=1,
                default=str(self.player.points),
            ),
        )
        self.max_points = discord.ui.Label(
            text="Peak Points",
            description=f"What is this player's peak points? (Current: {self.player.max_points})",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                min_length=1,
                default=str(self.player.max_points),
            ),
        )
        self.times_mvp = discord.ui.Label(
            text="Times MVP",
            description=f"How many times has this player been designated team MVP? (Current: {self.player.times_mvp})",
            component=discord.ui.TextInput(
                style=discord.TextStyle.short,
                min_length=1,
                default=str(self.player.times_mvp),
            ),
        )

        for item in [self.wins, self.losses, self.points, self.max_points, self.times_mvp]:
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Verify all provided fields are correct
        for key, value in self.new_stats.items():
            # Must be int castable
            assert isinstance(value, int)
            
            # Must be non-negative
            if key in ["wins", "losses", "times_mvp"]:
                assert value >= 0

            # Max points must be at least equal to current points
            if key == "max_points":
                assert value >= self.new_stats["points"]

        # Mark apply_edits as True after passed verification
        self.apply_edits = True

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        self.bot.logger.error(
            f"An exception occurred when trying to edit player stats: {error}"
        )
        traceback.print_exception(type(error), error, error.__traceback__)
        await interaction.response.send_message(Canned.ERR_STATS_PLAYER_EDIT)
