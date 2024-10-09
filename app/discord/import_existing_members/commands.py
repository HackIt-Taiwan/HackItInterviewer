# app/discord/import_existing_members/commands.py
import discord

from .helpers import EXECUTOR_DISCORD_ID, has_submitted_form
from .views import CollectExistingMemberInfoView


def setup(bot):
    """Set up the import_existing_members command."""

    @bot.command(name="import_existing_members")
    async def import_existing_members(ctx, user: discord.Member):
        """Command to start the import process for existing members."""
        await ctx.message.delete()
        # if str(ctx.author.id) != EXECUTOR_DISCORD_ID:
        #     await ctx.send("你無權使用此命令。")
        #     return

        if has_submitted_form(user.id):
            await ctx.send(f"{user.mention} 已經填寫過表單，不能再次填寫。")
            return

        view = CollectExistingMemberInfoView(user.id)
        await ctx.send(f"請 {user.mention} 點擊下面的按鈕開始填寫表單", view=view)
