# app/discord/customs/modals.py
import os
import discord
from flask import jsonify
import requests

from app.utils.db import get_staff


class PassportCheck(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(title="查驗護照", *args, **kwargs)
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
        if not is_valid or not applicant or not applicant.json().get("data"):
            await interaction.response.send_message("查驗失敗，並非有效的驗證資訊，請與 official@hackit.tw 聯繫。", ephemeral=True)
            return
        
        data = applicant.json().get("data")
        if not data or data[0].get("real_name") != self.children[0].value:
            await interaction.response.send_message("查驗失敗，並非有效的驗證資訊，請與 official@hackit.tw 聯繫。", ephemeral=True)
            return

        form_response = {
            "discord_id": str(user.id),
            "permission_level": 3,
        }

        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}

        response = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/update/{self.children[1].value}",
            headers=headers,
            json=form_response,
        )

        if response.status_code != 200:
            print(response.text)
            await interaction.response.send_message("查驗失敗，並非有效的驗證資訊，請與 official@hackit.tw 聯繫。", ephemeral=True)
            return
        
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=os.getenv("DISCORD_STAFF_ROLE_NAME"))

        if role:
            await user.add_roles(role) 
            await interaction.response.send_message("查驗成功，你現在正式加入這個伺服器了!", ephemeral=True)
        else:
            await interaction.response.send_message("查驗成功，但無法找到指定角色。請聯繫管理員協助。", ephemeral=True)