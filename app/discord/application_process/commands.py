# app/discord/application_process/commands.py
from discord.ext import commands

from app.models.form_response import FormResponse
from app.models.staff import Staff
from .helpers import send_initial_embed


def setup(bot):
    """Set up the application_process module."""

    @bot.command(name="process_application")
    async def process_application(ctx, application_uuid: str):
        """Manually process an application by UUID."""
        # Only users with sufficient permissions can execute this command
        discord_user_id = str(ctx.author.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await ctx.send("你無權使用此命令。")
            return

        form_response = FormResponse.objects(uuid=application_uuid).first()
        if not form_response:
            await ctx.send("找不到該申請。")
            return

        await send_initial_embed(form_response)
        await ctx.send("已發送申請處理消息。")
