# app/discord/customs/views.py
import discord

from app.discord.customs.modals import PassportCheck


class CustomsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="驗證",  custom_id="customs_view", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.custom_id == "customs_view":
            await interaction.response.send_modal(PassportCheck())
