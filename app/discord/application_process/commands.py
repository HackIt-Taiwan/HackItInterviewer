# app/discord/application_process/commands.py
from discord.ext import commands

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff
from .helpers import send_initial_embed, truncate
import discord


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

    @bot.command(name="find-my")
    async def find_my(ctx):
        """Display current applications the user is handling and all unaccepted cases."""
        discord_user_id = str(ctx.author.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff:
            await ctx.send("你還不是系統中的工作人員。")
            return

        # Get applications the user is handling
        user_apps = FormResponse.objects(
            manager_id=str(staff.uuid),
            interview_status__nin=[
                InterviewStatus.CANCELLED,
                InterviewStatus.INTERVIEW_PASSED,
                InterviewStatus.INTERVIEW_FAILED,
            ],
        )
        # Get all unaccepted applications
        unaccepted_apps = FormResponse.objects(
            interview_status=InterviewStatus.NOT_ACCEPTED
        )

        embeds = []
        description = ""
        max_length = 1024 - 80

        if user_apps:
            description += "**你負責的申請：**\n"
            for app in user_apps:
                line = f"{app.name} -- {app.interview_status.value} -- {app.email} -- {', '.join(app.interested_fields)}\n"
                if len(description) + len(line) > max_length:
                    embed = discord.Embed(description=description)
                    embeds.append(embed)
                    description = ""
                description += line

        if unaccepted_apps:
            if description:
                if len(description) + len("**未受理的申請：**\n") > max_length:
                    embed = discord.Embed(description=description)
                    embeds.append(embed)
                    description = ""
            description += "**未受理的申請：**\n"
            for app in unaccepted_apps:
                line = f"{app.name} -- {app.interview_status.value} -- {app.email} -- {', '.join(app.interested_fields)}\n"
                if len(description) + len(line) > max_length:
                    embed = discord.Embed(description=description)
                    embeds.append(embed)
                    description = ""
                description += line

        if description:
            embed = discord.Embed(description=description)
            embeds.append(embed)

        if not embeds:
            await ctx.send("沒有找到任何申請。")
        else:
            for embed in embeds:
                await ctx.send(embed=embed)
