# app/discord/customs/modals.py
import os
import discord
from flask import jsonify
import requests

from app.utils.db import get_staff

group = {
    "行政部": [os.getenv("AD_ROLE")],
    "策劃部": [os.getenv("PD_ROLE")],
    "資訊科技部": [os.getenv("ITD_ROLE")],
    "公共事務部": [os.getenv("PAD_ROLE")],
    "媒體影像部": [os.getenv("MVAD_ROLE")],

    "企劃組": [os.getenv("PD_ROLE"), os.getenv("PG_ID")],
    "進度管理組": [os.getenv("PD_ROLE"), os.getenv("PMG_ID")],

    "視覺影像組": [os.getenv("MVAD_ROLE"), os.getenv("VAG_ID")],
    "平面設計組": [os.getenv("MVAD_ROLE"),  os.getenv("GDG_ID")],

    "公關組": [os.getenv("PAD_ROLE"),  os.getenv("PRG_ID")],
    "社群管理組": [os.getenv("PAD_ROLE"), os.getenv("CMG_ID")],
}

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

        current_group = data[0].get("current_group")
        if current_group == "pending":
            await interaction.response.send_message("查驗失敗，請先填寫完你的個人訊息(第二部分表單後在進行驗證)，如有更多問題請與official@hackit.tw 聯繫。", ephemeral=True)
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

        real_name = data[0].get("real_name")
        nickname = data[0].get("nickname")

        if nickname and real_name:
            if len(nickname) + len(real_name) + 3 > 32:
                nickname = nickname[:32 - len(real_name) - 4] + "…"

        try:
            if real_name != nickname:
                await user.edit(nick=f"{nickname} ({real_name})")
            else:
                await user.edit(nick=real_name)
        except discord.Forbidden:
            print("無法修改暱稱：權限不足。")
            await interaction.response.send_message("查驗成功，但無法設定暱稱，請聯繫管理員協助。", ephemeral=True)
        except discord.HTTPException as e:
            print(f"設定暱稱時出現 HTTP 錯誤: {e}")
            await interaction.response.send_message("查驗成功，但無法設定暱稱，請聯繫管理員協助。", ephemeral=True)

        guild = interaction.guild
        role_id = int(os.getenv("DISCORD_STAFF_ROLE_ID"))
        role = discord.utils.get(guild.roles, id=role_id)

        group_roles = group[current_group]

        if role:
            await user.add_roles(role)

            for group_role_id in group_roles:
                if group_role_id: 
                    try:
                        group_role = discord.utils.get(guild.roles, id=int(group_role_id))
                        if group_role:
                            await user.add_roles(group_role)
                        else:
                            print(f"無法找到角色 ID: {group_role_id}")
                    except Exception as e:
                        print(f"添加角色 {group_role_id} 時出現錯誤: {e}")

            await interaction.response.send_message("查驗成功，你現在正式加入 HackIt 並獲得所有角色了!", ephemeral=True)
        else:
            await interaction.response.send_message("查驗成功，但無法找到主要身份組角色。請聯繫管理員協助。", ephemeral=True)