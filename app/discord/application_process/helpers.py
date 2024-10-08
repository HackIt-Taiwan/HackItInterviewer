# app/discord/application_process/helpers.py
import io
import os
import time
from datetime import datetime

import discord

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff

APPLY_FORM_CHANNEL_ID = int(os.getenv("APPLY_FORM_CHANNEL_ID", "0"))
APPLY_LOG_CHANNEL_ID = int(os.getenv("APPLY_LOG_CHANNEL_ID", "0"))


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
        InterviewStatus.NOT_ACCEPTED: 0xFF0000,  # Red
        InterviewStatus.NOT_CONTACTED: 0xFF4500,  # Orange
        InterviewStatus.EMAIL_SENT: 0xFF4500,  # Orange
        InterviewStatus.INTERVIEW_SCHEDULED: 0x3498DB,  # Blue
        InterviewStatus.NO_SHOW: 0xE74C3C,  # Red
        InterviewStatus.INTERVIEW_FAILED: 0xE74C3C,  # Red
        InterviewStatus.CANCELLED: 0xE74C3C,  # Red
        InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM: 0x9B59B6,  # Purple
        InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM: 0x9B59B6,  # Purple
        InterviewStatus.INTERVIEW_PASSED: 0x2ECC71,  # Green
        InterviewStatus.TRANSFERRED_TO_ANOTHER_TEAM: 0xF1C40F,  # Yellow
    }
    return status_colors.get(interview_status, 0x95A5A6)  # Default gray


def is_authorized(user, form_response):
    """Check if the user is authorized to perform actions on this form."""
    discord_user_id = str(user.id)
    staff = Staff.objects(discord_user_id=discord_user_id).first()
    if not staff:
        return False

    if str(staff.uuid) == form_response.manager_id or staff.permission_level >= 3:
        return True
    return False


async def send_initial_embed(form_response: FormResponse):
    """Send the initial embed to the apply form channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Create the embed
    embed = discord.Embed(
        title="新申請：等待受理",
        description="有一個新的申請等待受理。",
        color=get_embed_color(form_response.interview_status),
    )
    embed.set_footer(text=time.strftime('%Y/%m/%d %H:%M') + " ● HackIt")

    # Add fields to the embed
    fields_info = {
        'uuid': '申請識別碼',
        'interview_status': '申請狀態',
        'name': '姓名',
        'email': '電子郵件',
        'phone_number': '電話號碼',
        'interested_fields': '申請組別',
        'high_school_stage': '高中階段',
        'city': '城市',
        'preferred_order': '順序偏好',
        'reason_for_choice': '選擇原因',
        'related_experience': '相關經驗',
    }

    embed_fields = ['uuid', 'interview_status', 'name', 'email', 'phone_number', 'interested_fields']
    full_content = _generate_full_content(fields_info, form_response)

    # Attach full content as a file
    file_stream = io.StringIO(full_content)
    file = discord.File(fp=file_stream, filename=f"application_{form_response.uuid}.txt")

    # Add fields to the embed
    for field in embed_fields:
        value = getattr(form_response, field, None)
        if field == 'interview_status':
            # Use Enum's value to get the Chinese translation for interview status
            value = form_response.interview_status.value
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(name=fields_info[field], value=truncate(str(value)), inline=False)


    # Create view with buttons
    from .views import AcceptOrCancelView

    view = AcceptOrCancelView(form_response)

    message = await channel.send(embed=embed, file=file, view=view)

    form_response.last_message_id = str(message.id)
    form_response.save()


async def send_log_message(form_response: FormResponse, title: str, current_group: str = None, reason: str = None):
    """Send a log message to the APPLY_LOG_CHANNEL_ID channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_LOG_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_LOG_CHANNEL_ID} not found.")
        return

    staff = Staff.objects(uuid=form_response.manager_id).first()
    
    if not staff:
        embed = discord.Embed(
            title=title,
            description=f"申請流程已更新",
            color=get_embed_color(form_response.interview_status),
        )
    else:
        discord_user = await bot.fetch_user(staff.discord_user_id)
        embed = discord.Embed(
            title=title,
            description=f"申請流程已更新 cc:{discord_user.mention}",
            color=get_embed_color(form_response.interview_status),
        )

    embed.set_footer(text=time.strftime('%Y/%m/%d %H:%M') + " ● HackIt")


    # Add fields to the embed
    fields_info = {
        'uuid': '申請識別碼',
        'interview_status': '申請狀態',
        'name': '姓名',
        'email': '電子郵件',
        'phone_number': '電話號碼',
        'interested_fields': '申請組別',
        'high_school_stage': '高中階段',
        'city': '城市',
        'preferred_order': '順序偏好',
        'reason_for_choice': '選擇原因',
        'related_experience': '相關經驗',
    }

    embed_fields = ['uuid', 'interview_status', 'name', 'email']
    full_content = _generate_full_content(fields_info, form_response)

    # Add fields to the embed
    for field in embed_fields:
        value = getattr(form_response, field, None)
        if field == 'interview_status':
            # Use Enum's value to get the Chinese translation for interview status
            value = form_response.interview_status.value
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(name=fields_info[field], value=truncate(str(value)), inline=False)


    if current_group:
        embed.add_field(name="加入組別", value=current_group, inline=False)

    # Add history
    if form_response.history:
        history_str = "\n".join(form_response.history)
        embed.add_field(name="歷史紀錄", value=history_str, inline=False)

    if reason:
        embed.add_field(name="原因", value=truncate(reason), inline=False)
        full_content += f"\n\n決議原因:\n {reason}\n"

    # Attach full content as a file
    file_stream = io.StringIO(full_content)
    file = discord.File(fp=file_stream, filename=f"application_{form_response.uuid}.txt")

    await channel.send(embed=embed, file=file)


def get_view_for_stage(form_response: FormResponse):
    """Return the appropriate view based on the current stage."""
    from .views import (
        ContactOrFailView,
        ArrangeOrCancelView,
        AttendOrNoShowView,
        ManagerFillFormView,
    )

    status = form_response.interview_status

    if status == InterviewStatus.NOT_CONTACTED:
        return ContactOrFailView(form_response)
    elif status == InterviewStatus.EMAIL_SENT:
        return ArrangeOrCancelView(form_response)
    elif status == InterviewStatus.INTERVIEW_SCHEDULED:
        return AttendOrNoShowView(form_response)
    elif status == InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM:
        return ManagerFillFormView(form_response)
    else:
        return None  # No buttons needed


async def send_stage_embed(form_response: FormResponse, user):
    """Sends an embed for the current application stage.

    Args:
        form_response (FormResponse): The response object containing form data.
        user: The user who submitted the form.
    """
    bot = get_bot()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Stage titles mapping
    stage_titles = {
        InterviewStatus.NOT_CONTACTED: "Stage 2: 等待聯繫",
        InterviewStatus.EMAIL_SENT: "Stage 3: 試圖安排面試",
        InterviewStatus.INTERVIEW_SCHEDULED: "Stage 4: 面試已安排",
        InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM: "Stage 6: 負責人填寫資料",
    }

    staff = Staff.objects(uuid=form_response.manager_id).first()
    if not staff:
        print(f"Staff with ID {form_response.manager_id} not found.")
        await channel.send("錯誤，找不到負責人。")
    discord_user = await bot.fetch_user(staff.discord_user_id)

    # Create the embed
    embed_title = stage_titles.get(form_response.interview_status, "申請進度更新")
    embed = discord.Embed(
        title=embed_title,
        # and @ the user for manager_id
        description=f"申請進度已更新 cc:{discord_user.mention}",
        color=get_embed_color(form_response.interview_status),
    )
    embed.set_footer(text=time.strftime('%Y/%m/%d %H:%M') + " ● HackIt")

    fields_info = {
        'uuid': '申請識別碼',
        'interview_status': '申請狀態',
        'name': '姓名',
        'email': '電子郵件',
        'phone_number': '電話號碼',
        'interested_fields': '申請組別',
        'high_school_stage': '高中階段',
        'city': '城市',
        'preferred_order': '順序偏好',
        'reason_for_choice': '選擇原因',
        'related_experience': '相關經驗',
    }

    embed_fields = ['uuid', 'interview_status', 'name', 'email', 'phone_number', 'interested_fields']
    full_content = _generate_full_content(fields_info, form_response)

    # Attach full content as a file
    file_stream = io.StringIO(full_content)
    file = discord.File(fp=file_stream, filename=f"application_{form_response.uuid}.txt")

    # Add fields to the embed
    for field in embed_fields:
        value = getattr(form_response, field, None)
        if field == 'interview_status':
            # Use Enum's value to get the Chinese translation for interview status
            value = form_response.interview_status.value
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            embed.add_field(name=fields_info[field], value=truncate(str(value)), inline=False)


    view = get_view_for_stage(form_response)
    message = await channel.send(embed=embed, view=view, file=file)

    form_response.last_message_id = str(message.id)
    form_response.save()

def _generate_full_content(fields_info, form_response):
    """Generates the full content for the file to be attached.

    Args:
        fields_info (dict): A dictionary of field names and their display names.
        form_response (FormResponse): The response object.

    Returns:
        str: The full content for the file.
    """
    content = ""
    for field, display_name in fields_info.items():
        value = getattr(form_response, field, None)
        if field == 'interview_status':
            # Use Enum's value to get the Chinese translation for interview status
            value = form_response.interview_status.value
        if value:
            if isinstance(value, list):
                value = ", ".join(value)
            content += f"{display_name}: {value}\n"

    if form_response.history:
        content += "\n歷史紀錄:\n" + "\n".join(form_response.history)

    return content
