# app/discord/customs/commands.py
import os
import time

import discord

from app.discord.customs.views import CustomsView

def setup(bot):
    """Set up the customs module."""

    @bot.command(name="find_my_setup_customs")
    async def find_my_setup_customs(ctx):
        await ctx.message.delete()
        if str(ctx.author.id) != os.getenv("EXECUTOR_DISCORD_ID"):
            await ctx.send("你無權使用此命令。")
            return

        today = time.strftime('%Y/%m/%d')
        embed = discord.Embed(
            title="HackIt | 工作人員驗證",
            description="為了確保伺服器的安全及省去相關行政操作\n本 Discord 伺服器採用自動化認證系統\n在開始身份驗證之前請先準備好您的姓名及您的團員識別碼，具體說明請查看\nhttps://go.hackit.tw/passport-check\n點擊下方「驗證」後開始身份驗證，完成後您便可自由暢覽整個伺服器",
            colour=0x00FF00)
        embed.set_footer(text=today + " ● HackIt")
        await ctx.send(embed=embed, view=CustomsView())