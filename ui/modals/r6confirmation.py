import discord


class R6ConfirmationModal(discord.ui.Modal):
    def __init__(self, *, operation: str):
        super().__init__(title=f"{operation.title()} Confirmation")

        self.init_components()
        self.proceed = False

    def init_components(self) -> None:
        self.confirm = discord.ui.Label(
            text="Are you sure?",
            description="This operation cannot be undone. Only proceed if you know what you are doing.",
            component=discord.ui.Select(
                options=[
                    discord.SelectOption(label="Yes, proceed", value="1"),
                    discord.SelectOption(label="No, cancel", value="0"),
                ]
            )
        )
        self.add_item(self.confirm)

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.confirm.component, discord.ui.Select)

        self.proceed = int(self.confirm.component.values[0]) == 1
        await interaction.response.defer()
