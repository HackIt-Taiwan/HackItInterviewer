# app/discord/application_process/commands.py
import os

import discord
from .views import FindMyView


def setup(bot):
    """Set up the application_process module."""

    @bot.command(name="find_my_setup")
    async def find_my_setup(ctx):
        """Command to start the import process for existing members."""
        await ctx.message.delete()
        if str(ctx.author.id) != os.getenv("EXECUTOR_DISCORD_ID"):
            await ctx.send("你無權使用此命令。")
            return

        view = FindMyView()
        embed = discord.Embed(
            title="面試表單管理功能",
            color=0xFF4500,
        )
        embed.add_field(
            name="查找負責案件",
            value="查詢您負責的處理中面試表單。",
            inline=False,
        )
        embed.add_field(
            name="查找未受理案件",
            value="查詢所有未受理的面試表單。",
            inline=False,
        )
        await ctx.send(embed=embed, view=view)