# app/discord/customs/modals.py
import discord

from app.utils.db import get_staff


class PassportCheck(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.TextInput(
            label='姓名',
            placeholder="於申請表單上所填寫的姓名",
            style=discord.TextStyle.short
        ))

        self.add_item(discord.ui.TextInput(
            label='團員識別碼',
            placeholder="隨附於 HackIt 發送的招募結果通知信建中",
            style=discord.TextStyle.short
        ))

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user

        payload = {"uuid": self.children[1].value}
        is_valid, applicant = get_staff(payload)
        if not is_valid:
            await interaction.response.send_message("查驗失敗，您並非有效公民，請與 official@hackit.tw 聯繫。", ephemeral=True)
            return

        # TODO: use applicant match the name, and check are they pass interviewer? last, check do they already have a discord connection?
        # TODO: if pass, set the role(department,group) to the user and change the nickname to the name

        await interaction.response.send_message("查驗成功，您為合格公民。", ephemeral=True)