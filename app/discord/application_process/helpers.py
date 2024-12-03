# app/discord/application_process/helpers.py
import os
import time

import discord

from app.utils.db import get_staff, update_staff
from app.utils.mail_sender import send_email
from app.utils.jwt import generate_data_token

APPLY_FORM_CHANNEL_ID = int(os.getenv("APPLY_FORM_CHANNEL_ID"))
APPLY_LOG_CHANNEL_ID = int(os.getenv("APPLY_LOG_CHANNEL_ID"))


def truncate(value, max_length=1024):
    """Truncate a string to the specified maximum length."""
    if len(value) > max_length:
        return value[: max_length - 80] + "...（過長無法顯示）"
    return value


def get_bot():
    """Retrieve the bot instance from the global scope."""
    from app.discord.bot_module import bot

    return bot


def get_embed_color(interview_status):
    """Return the color for the embed based on the interview status."""
    status_colors = {
        # --interactive--
        "NEW_APPLICATION": 0x9B59B6,  # Purple
        "ACCEPTED_STAGE1_APPLICANT": 0x9B59B6,  # Purple
        # --logging--
        "NOT_ACCEPTED": 0xFF0000,  # Red
        "ACCEPTED": 0x2ECC71,  # Green
        "INTERVIEW_FAILED": 0xE74C3C,  # Red
        "INTERVIEW_CANCELLED": 0xE74C3C,  # Red
        "INTERVIEW_PASSED": 0x2ECC71,  # Green
    }
    return status_colors.get(interview_status, 0x95A5A6)  # Default gray


def get_embed_title(action):
    """Returns the title for embed based on action"""
    titles = {
        "NOT_ACCEPTED": "申請已拒絕",  # Red
        "ACCEPTED": "申請已接受",  # Green
        "INTERVIEW_FAILED": "面試未通過",  # Red
        "INTERVIEW_CANCELLED": "面試取消",  # Red
        "INTERVIEW_PASSED": "面試已通過/已接受",  # Green
    }
    return titles.get(action, "申請流程")


async def send_initial_embed(form_response):
    """Send the initial embed to the apply form channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Create the embed
    # if form_response.is_duplicate:
    #     embed = discord.Embed(
    #         title="新申請：重複申請",
    #         description="有一個重複的申請已被收到。",
    #         color=0xF1C40F,
    #     )
    embed = discord.Embed(
        title="新申請：等待受理",
        description="有一個新的申請等待受理。",
        color=get_embed_color("NEW_APPLICATION"),
    )

    embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")

    # Add fields to the embed
    fields_info = {
        "uuid": "申請識別碼",
        "real_name": "姓名",
        "email": "電子郵件",
        "phone_number": "電話號碼",
        "interested_fields": "申請組別",
        "high_school_stage": "高中階段",
        "city": "城市",
    }

    embed_fields = [
        "uuid",
        "real_name",
        "email",
        "phone_number",
        "interested_fields",
    ]

    # Add fields to the embed
    for field in embed_fields:
        value = form_response.get(field)
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(
                name=fields_info[field], value=truncate(str(value)), inline=False
            )

    # Add detailed data about applicant
    jwt = generate_data_token(form_response.get("uuid"))
    embed.add_field(
        name="申請者資料",
        value=f"{os.getenv("DOMAIN")}/apply/applicant_data/{jwt}",
        inline=False,
    )

    # Create view with buttons
    from .views import AcceptOrCancelView

    view = AcceptOrCancelView()

    message = await channel.send(embed=embed, view=view)

    send_email(
        subject="Counterspell / 已收到您的工作人員報名表！",
        recipient=form_response.get("email"),
        template="emails/notification_email.html",
        name=form_response.get("real_name"),
        uuid=form_response.get("uuid"),
    )

    # Update applicant's assignee
    payload = {
        "apply_message": f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}",
    }
    update_staff(form_response.get("uuid"), payload)


async def send_stage_embed(applicant, user):
    """Sends an embed for next application stage."""
    bot = get_bot()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    payload = {"discord_id": str(user.id)}
    is_valid, staff = get_staff(payload)
    if not is_valid:
        print(f"Staff with ID {user.id} not found.")
        await channel.send("錯誤，找不到負責人。")
    discord_user = await bot.fetch_user(user.id)

    # Create the embed
    embed_title = "Stage 2: 申請進度更新"
    embed = discord.Embed(
        title=embed_title,
        # and @ the user for manager_id
        description=f"申請進度已更新 cc:{discord_user.mention}",
        color=get_embed_color("ACCEPTED_STAGE1_APPLICANT"),
    )
    embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")

    fields_info = {
        "uuid": "申請識別碼",
        "real_name": "姓名",
        "email": "電子郵件",
        "phone_number": "電話號碼",
        "interested_fields": "申請組別",
        "high_school_stage": "高中階段",
        "city": "城市",
    }

    embed_fields = [
        "uuid",
        "real_name",
        "email",
        "phone_number",
        "interested_fields",
    ]

    # Add fields to the embed
    for field in embed_fields:
        value = applicant.get(field)
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(
                name=fields_info[field], value=truncate(str(value)), inline=False
            )

    # Add detailed data about applicant
    jwt = generate_data_token(applicant.get("uuid"))
    embed.add_field(
        name="申請者資料",
        value=f"{os.getenv("DOMAIN")}/apply/applicant_data/{jwt}",
        inline=False,
    )

    # Create view with buttons
    from .views import InterviewResultView

    view = InterviewResultView()
    message = await channel.send(embed=embed, view=view)

    # Send log message
    await send_log_message(
        applicant,
        discord_user,
        action="ACCEPTED",
    )

    # Update applicant's assignee
    payload = {
        "team_leader": str(user.id),
        "apply_message": f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}",
    }
    update_staff(applicant.get("uuid"), payload)


async def send_log_message(
    form_response,
    user,
    action,
    reason: str = None,
):
    """Send a log message to the APPLY_LOG_CHANNEL_ID channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_LOG_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_LOG_CHANNEL_ID} not found.")
        return

    discord_user = await bot.fetch_user(user.id)
    embed = discord.Embed(
        title=get_embed_title(action),
        description=f"申請流程已更新 by:{discord_user.mention}",
        color=get_embed_color(action),
    )

    embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")

    # Add fields to the embed
    fields_info = {
        "uuid": "申請識別碼",
        "name": "姓名",
        "email": "電子郵件",
    }

    embed_fields = ["uuid", "name", "email"]

    # Add fields to the embed
    for field in embed_fields:
        value = getattr(form_response, field, None)
        if field == "interview_status":
            # Use Enum's value to get the Chinese translation for interview status
            value = form_response.interview_status.value
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(
                name=fields_info[field], value=truncate(str(value)), inline=False
            )

    if reason:
        embed.add_field(name="理由", value=truncate(str(reason)), inline=False)

    # Send the message to the log channel with the button
    await channel.send(embed=embed)
