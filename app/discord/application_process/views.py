# app/discord/application_process/views.py
import io

import discord
from discord.ui import Button, View
from datetime import datetime

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff

from .helpers import (
    truncate,
    get_bot,
    get_embed_color,
    APPLY_FORM_CHANNEL_ID,
    send_stage_embed, _generate_full_content,
)
from .modals import (
    FailureReasonModal,
    TransferToTeamModal,
    ManagerFillInfoModal1,
    is_authorized,
)


class FormResponseView(View):
    """Base View that handles form_response retrieval."""

    def __init__(self, form_response=None):
        super().__init__(timeout=None)
        self.form_response = form_response

    async def ensure_form_response(self, interaction: discord.Interaction):
        """Ensure self.form_response is set, retrieving it from the database if necessary."""
        if self.form_response is None:
            last_message_id = str(interaction.message.id)
            self.form_response = FormResponse.objects(last_message_id=last_message_id).first()
            if not self.form_response:
                await interaction.response.send_message("表單資料未找到。", ephemeral=True)
                return False
        return True


class AcceptOrCancelView(FormResponseView):
    """View with Accept and Cancel buttons for Stage 1."""

    @discord.ui.button(
        label="受理",
        style=discord.ButtonStyle.success,
        custom_id="accept_or_cancel_view_accept",
    )
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        """Handle Accept button click."""
        if button.custom_id != "accept_or_cancel_view_accept":
            return

        if not await self.ensure_form_response(interaction):
            return

        # Check permission level of the user
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Update form_response
        self.form_response.manager_id = str(staff.uuid)
        self.form_response.interview_status = InterviewStatus.NOT_CONTACTED
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 受理 by {interaction.user.name}"

        if not self.form_response.history:
            self.form_response.history = []
        self.form_response.history.append(history_entry)
        self.form_response.save()

        # Proceed to next stage
        await interaction.response.send_message("已受理，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="accept_or_cancel_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if button.custom_id != "accept_or_cancel_view_cancel":
            return

        if not await self.ensure_form_response(interaction):
            return

        # Identity verification
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal to input cancellation reason
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


def get_view_for_stage(form_response: FormResponse):
    """Return the appropriate view based on the current stage."""
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


class ContactOrFailView(FormResponseView):
    """View for Stage 2: Waiting to Contact."""

    @discord.ui.button(
        label="已聯繫",
        style=discord.ButtonStyle.success,
        custom_id="contact_or_fail_view_contacted",
    )
    async def contacted_button(self, interaction: discord.Interaction, button: Button):
        """Handle Contacted button click."""
        if not await self.ensure_form_response(interaction):
            return

        # Check if the user is the manager
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        self.form_response.is_email_contacted = True
        self.form_response.interview_status = InterviewStatus.EMAIL_SENT
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 已聯繫 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        await interaction.response.send_message("已聯繫，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="面試失敗",
        style=discord.ButtonStyle.danger,
        custom_id="contact_or_fail_view_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="已取消",
        style=discord.ButtonStyle.danger,
        custom_id="contact_or_fail_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


class ArrangeOrCancelView(FormResponseView):
    """View for Stage 3: Attempting to Arrange Interview."""

    @discord.ui.button(
        label="已安排",
        style=discord.ButtonStyle.success,
        custom_id="arrange_or_cancel_view_arranged",
    )
    async def arranged_button(self, interaction: discord.Interaction, button: Button):
        """Handle Arranged button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        self.form_response.is_interview_scheduled = True
        self.form_response.interview_status = InterviewStatus.INTERVIEW_SCHEDULED
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 已安排面試 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        await interaction.response.send_message("已安排面試，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="已取消",
        style=discord.ButtonStyle.danger,
        custom_id="arrange_or_cancel_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


class AttendOrNoShowView(FormResponseView):
    """View for Stage 4: Interview Arranged."""

    @discord.ui.button(
        label="已出席",
        style=discord.ButtonStyle.success,
        custom_id="attend_or_no_show_view_attended",
    )
    async def attended_button(self, interaction: discord.Interaction, button: Button):
        """Handle Attended button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        self.form_response.is_attended_interview = True
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 面試已出席 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        # Proceed to next stage
        await interaction.response.send_message("面試已出席，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        # Send the interview result embed
        await send_interview_result_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="未出席",
        style=discord.ButtonStyle.secondary,
        custom_id="attend_or_no_show_view_no_show",
    )
    async def no_show_button(self, interaction: discord.Interaction, button: Button):
        """Handle No Show button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        self.form_response.interview_status = InterviewStatus.NO_SHOW
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 未出席面試 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        # Go back to Stage 3
        await interaction.response.send_message("未出席面試，返回安排面試階段。", ephemeral=True)
        await interaction.message.delete()
        self.form_response.interview_status = InterviewStatus.EMAIL_SENT
        await send_stage_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="attend_or_no_show_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


async def send_interview_result_embed(form_response: FormResponse, user):
    """Send the embed for interview result stage."""
    bot = get_bot()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Create the embed
    embed = discord.Embed(
        title="Stage 5: 面試結果",
        description="請選擇面試結果。",
        color=get_embed_color(form_response.interview_status),
        timestamp=datetime.utcnow(),
    )

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

    view = InterviewResultView(form_response)
    message = await channel.send(embed=embed, view=view, file=file)
    form_response.last_message_id = str(message.id)
    form_response.save()


class InterviewResultView(FormResponseView):
    """View for Stage 5: Interview Result."""

    @discord.ui.button(
        label="面試通過",
        style=discord.ButtonStyle.success,
        custom_id="interview_result_view_pass",
    )
    async def pass_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Passed button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        self.form_response.interview_status = InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 面試通過 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        await interaction.response.send_message("面試通過，請填寫資料。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(self.form_response, interaction.user)

    @discord.ui.button(
        label="面試失敗",
        style=discord.ButtonStyle.danger,
        custom_id="interview_result_view_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="轉接至他組",
        style=discord.ButtonStyle.secondary,
        custom_id="interview_result_view_transfer",
    )
    async def transfer_button(self, interaction: discord.Interaction, button: Button):
        """Handle Transfer to Another Team button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        modal = TransferToTeamModal(self.form_response)
        await interaction.response.send_modal(modal)


class ManagerFillFormView(FormResponseView):
    """View for Stage 6: Manager Fills in Information."""

    @discord.ui.button(
        label="填寫資料",
        style=discord.ButtonStyle.primary,
        custom_id="manager_fill_form_view_fill_form",
    )
    async def fill_form_button(self, interaction: discord.Interaction, button: Button):
        """Handle Fill Form button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal for manager to fill in information
        modal = ManagerFillInfoModal1(self.form_response)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="manager_fill_form_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not await self.ensure_form_response(interaction):
            return

        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)

class FindMyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="查找負責案件", style=discord.ButtonStyle.primary, custom_id="find_my_button")
    async def find_my_button(self, interaction: discord.Interaction, button: Button):
        """Handle the button interaction to trigger the find-my logic."""
        if button.custom_id != "find_my_button":
            return

        print(interaction.user.id)
        staff_member = Staff.objects(discord_user_id=str(interaction.user.id)).first()
        print(staff_member.uuid)
        if staff_member is None:
            no_staff_embed = discord.Embed(description=f"使用者 {interaction.user.mention} 越權查詢！", color=0xff6666)
            await interaction.response.send_message(embed=no_staff_embed, ephemeral=True)
            return

        user_apps = FormResponse.objects(
            manager_id=str(staff_member.uuid),
            interview_status__nin=[
                InterviewStatus.CANCELLED,
                InterviewStatus.INTERVIEW_PASSED,
                InterviewStatus.INTERVIEW_FAILED,
            ],
        )

        if not user_apps:
            no_cases_embed = discord.Embed(description="目前沒有負責的案件。", color=0xff6666)
            await interaction.response.send_message(embed=no_cases_embed, ephemeral=True)
            return

        embeds = []
        description = ""
        max_length = 1024 - 80

        for app in user_apps:

            # Construct the message link
            if app.last_message_id:
                message_link = f"https://discord.com/channels/{interaction.guild.id}/{APPLY_FORM_CHANNEL_ID}/{app.last_message_id}"
                message_jump = f"[跳轉到訊息]({message_link})"
            else:
                message_jump = "無法取得訊息連結"

            line = f"{app.name} -- {app.interview_status.value} -- {app.email} \n {', '.join(app.interested_fields)} / {message_jump}\n\n"
            if len(description) + len(line) > max_length:
                embed = discord.Embed(description=description, color=0x3498DB)
                embeds.append(embed)
                description = ""
            description += line

        if description:
            embed = discord.Embed(description=description)
            embeds.append(embed)

        for embed in embeds:
            await interaction.response.send_message(embed=embed, ephemeral=True)
