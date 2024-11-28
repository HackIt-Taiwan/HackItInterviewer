# app/discord/application_process/helpers.py
import io
import os
import time
import requests

import discord
from discord.ui import View, Button

from app.utils.mail_sender import send_email

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
        "ACCEPTED_APPLICANT": 0x9B59B6,  # Purple
        # --logging--
        "NOT_ACCEPTED": 0xFF0000,  # Red
        "ACCEPTED": 0x2ECC71,  # Green
        "INTERVIEW_FAILED": 0xE74C3C,  # Red
        "INTERVIEW_CANCELLED": 0xE74C3C,  # Red
        "INTERVIEW_PASSED": 0x2ECC71,  # Green
    }
    return status_colors.get(interview_status, 0x95A5A6)  # Default gray


def is_authorized(user, form_response):
    """Check if the user is authorized to perform actions on this form."""
    discord_user_id = str(user.id)
    payload = {"discord_id": discord_user_id}
    headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}
    staff = requests.post(
        url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/getstaffs",
        headers=headers,
        json=payload,
    )
    staff = staff.json().get("data")[0]

    if not staff:
        return False

    if str(staff.get("uuid")) == form_response.manager_id or staff.get("permission_level") >= 3:
        return True
    return False
    return True


async def send_initial_embed(form_response):
    """Send the initial embed to the apply form channel."""
    bot = get_bot()
    await bot.wait_until_ready()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    await channel.send("Test message to verify bot functionality.")

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
        "name": "姓名",
        "email": "電子郵件",
        "phone_number": "電話號碼",
        "interested_fields": "申請組別",
        "high_school_stage": "高中階段",
        "city": "城市",
    }

    embed_fields = [
        "uuid",
        "name",
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

    # # Create view with buttons
    from .views import AcceptOrCancelView

    view = AcceptOrCancelView()

    await channel.send(embed=embed, view=view)

    send_email(
        subject="Counterspell / 已收到您的工作人員報名表！",
        recipient=form_response.email,
        template="emails/notification_email.html",
        name=form_response.name,
        uuid=form_response.uuid,
    )


# async def send_log_message(
#     form_response: FormResponse,
#     title: str,
#     current_group: str = None,
#     reason: str = None,
#     apply_staff: Staff = None,
# ):
#     """Send a log message to the APPLY_LOG_CHANNEL_ID channel."""
#     bot = get_bot()
#     await bot.wait_until_ready()
#     channel = bot.get_channel(APPLY_LOG_CHANNEL_ID)
#     if channel is None:
#         print(f"Channel with ID {APPLY_LOG_CHANNEL_ID} not found.")
#         return
#
#     staff = Staff.objects(uuid=form_response.manager_id).first()
#
#     if not staff:
#         embed = discord.Embed(
#             title=title,
#             description=f"申請流程已更新",
#             color=get_embed_color(form_response.interview_status),
#         )
#     else:
#         discord_user = await bot.fetch_user(staff.discord_user_id)
#         embed = discord.Embed(
#             title=title,
#             description=f"申請流程已更新 cc:{discord_user.mention}",
#             color=get_embed_color(form_response.interview_status),
#         )
#
#     embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")
#
#     # Add fields to the embed
#     fields_info = {
#         "uuid": "申請識別碼",
#         "interview_status": "申請狀態",
#         "name": "姓名",
#         "email": "電子郵件",
#         "phone_number": "電話號碼",
#         "interested_fields": "申請組別",
#         "high_school_stage": "高中階段",
#         "city": "城市",
#         "preferred_order": "順序偏好",
#         "reason_for_choice": "選擇原因",
#         "related_experience": "相關經驗",
#     }
#
#     embed_fields = ["uuid", "interview_status", "name", "email"]
#     full_content = _generate_full_content(fields_info, form_response)
#
#     # Add fields to the embed
#     for field in embed_fields:
#         value = getattr(form_response, field, None)
#         if field == "interview_status":
#             # Use Enum's value to get the Chinese translation for interview status
#             value = form_response.interview_status.value
#         if value:
#             if isinstance(value, list):
#                 value = ", ".join(value)
#             embed.add_field(
#                 name=fields_info[field], value=truncate(str(value)), inline=False
#             )
#
#     if current_group:
#         embed.add_field(name="加入組別", value=current_group, inline=False)
#
#     # Add history
#     if form_response.history:
#         history_str = "\n".join(form_response.history)
#         embed.add_field(name="歷史紀錄", value=history_str, inline=False)
#
#     if reason:
#         # only fail has reason
#         embed.add_field(name="原因", value=truncate(reason), inline=False)
#         full_content += f"\n\n決議原因:\n {reason}\n"
#         view = SendNotificationButton(form_response, True, reason)
#     else:
#         view = SendNotificationButton(form_response, False, apply_staff=apply_staff)
#
#     # Attach full content as a file
#     file_stream = io.StringIO(full_content)
#     file = discord.File(
#         fp=file_stream, filename=f"application_{form_response.uuid}.txt"
#     )
#
#     # Create view with button to send email
#
#     # Send the message to the log channel with the button
#     await channel.send(embed=embed, file=file, view=view)


# class SendNotificationButton(View):
#     """View containing a button to send the recruitment result notification."""
#
#     def __init__(
#         self,
#         form_response: FormResponse,
#         fail: bool,
#         reason: str = None,
#         apply_staff: Staff = None,
#     ):
#         super().__init__(timeout=None)
#         self.form_response = form_response
#         self.fail = fail
#         self.reason = reason
#         self.mail_sent = False
#         self.apply_staff = apply_staff
#
#     @discord.ui.button(
#         label="發送招募結果通知",
#         style=discord.ButtonStyle.primary,
#         custom_id="send_email_button",
#     )
#     async def send_email_button(self, interaction: discord.Interaction, button: Button):
#         if button.custom_id != "send_email_button":
#             return
#
#         if self.mail_sent:
#             await interaction.response.send_message(
#                 "郵件已發送，無法重複發送。", ephemeral=True
#             )
#             return
#
#         if self.fail:
#             send_email(
#                 subject="Counterspell / 招募結果通知",
#                 recipient=self.form_response.email,
#                 template="emails/notification_fail.html",
#                 name=self.form_response.name,
#                 uuid=self.form_response.uuid,
#                 reason=self.reason,
#             )
#         else:
#             send_email(
#                 subject="Counterspell / 招募結果通知",
#                 recipient=self.apply_staff.email,
#                 template="emails/notification_pass.html",
#                 name=self.apply_staff.name,
#                 uuid=self.apply_staff.uuid,
#                 email=self.apply_staff.email,
#             )
#
#         self.mail_sent = True
#         button.disabled = True
#         await interaction.response.edit_message(view=self)
#
#     @discord.ui.button(
#         label="結果通知信預覽",
#         style=discord.ButtonStyle.secondary,
#         custom_id="preview_email_button",
#     )
#     async def preview_email_button(
#         self, interaction: discord.Interaction, button: Button
#     ):
#         if button.custom_id != "preview_email_button":
#             return
#
#         DOMAIN = os.getenv("DOMAIN", "https://interviewer.hackit.tw")
#
#         if self.fail:
#             preview_url = f"{DOMAIN}/admin/preview/email?email_template=emails/notification_fail.html&name={self.form_response.name}&uuid={self.form_response.uuid}&email={self.apply_staff.email}&reason={self.reason.replace('\n', '|')}"
#         else:
#             preview_url = f"{DOMAIN}/admin/preview/email?email_template=emails/notification_pass.html&name={self.apply_staff.name}&uuid={self.apply_staff.uuid}&email={self.apply_staff.email}"
#
#         await interaction.response.send_message(
#             f"點擊以下連結預覽通知信：\n[點擊我預覽]({preview_url})", ephemeral=True
#         )
