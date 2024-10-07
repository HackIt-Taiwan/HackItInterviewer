# app/discord/application_process/views.py
import discord
from discord.ui import Button, View

from app.models.form_response import FormResponse, InterviewStatus
from datetime import datetime

from .helpers import (
    truncate,
    get_bot,
    get_embed_color,
    APPLY_FORM_CHANNEL_ID,
)
from .modals import (
    FailureReasonModal,
    TransferToTeamModal,
    ManagerFillInfoModal1,
    is_authorized,
)
from ...models.staff import Staff


class AcceptOrCancelView(View):
    """View with Accept and Cancel buttons for Stage 1."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="受理", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        """Handle Accept button click."""
        # Check permission level of the user
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Set manager_id to the staff's uuid
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

    @discord.ui.button(label="取消", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        # Identity verification
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal to input cancellation reason
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


async def send_stage_embed(form_response: FormResponse, user):
    """Send the embed for the current stage."""
    bot = get_bot()
    channel = bot.get_channel(APPLY_FORM_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {APPLY_FORM_CHANNEL_ID} not found.")
        return

    # Create the embed
    stage_titles = {
        InterviewStatus.NOT_CONTACTED: "Stage 2: 等待聯繫",
        InterviewStatus.EMAIL_SENT: "Stage 3: 試圖安排面試",
        InterviewStatus.INTERVIEW_SCHEDULED: "Stage 4: 面試已安排",
        InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM: "Stage 6: 負責人填寫資料",
        InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM: "Stage 7: 等待申請者填寫資料",
    }

    embed = discord.Embed(
        title=stage_titles.get(form_response.interview_status, "申請進度更新"),
        description="申請進度已更新。",
        color=get_embed_color(form_response.interview_status),
        timestamp=datetime.utcnow(),
    )

    # Add fields to the embed
    fields = [
        ("申請識別碼", str(form_response.uuid)),
        ("申請狀態", form_response.interview_status.value),
        ("姓名", form_response.name),
        ("電子郵件", form_response.email),
        ("電話號碼", form_response.phone_number),
        ("高中階段", form_response.high_school_stage),
        ("城市", form_response.city),
        ("申請組別", ", ".join(form_response.interested_fields)),
        ("順序偏好", form_response.preferred_order),
        ("選擇原因", form_response.reason_for_choice),
    ]

    if form_response.related_experience:
        fields.append(("相關經驗", form_response.related_experience))

    for name, value in fields:
        if value:
            value = truncate(str(value))
            embed.add_field(name=name, value=value, inline=False)

    # Create view with buttons based on the current stage
    view = get_view_for_stage(form_response)

    await channel.send(embed=embed, view=view)


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


class ContactOrFailView(View):
    """View for Stage 2: Waiting to Contact."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="已聯繫", style=discord.ButtonStyle.success)
    async def contacted_button(self, interaction: discord.Interaction, button: Button):
        """Handle Contacted button click."""
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

    @discord.ui.button(label="面試失敗", style=discord.ButtonStyle.danger)
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="已取消", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


class ArrangeOrCancelView(View):
    """View for Stage 3: Attempting to Arrange Interview."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="已安排", style=discord.ButtonStyle.success)
    async def arranged_button(self, interaction: discord.Interaction, button: Button):
        """Handle Arranged button click."""
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

    @discord.ui.button(label="已取消", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)


class AttendOrNoShowView(View):
    """View for Stage 4: Interview Arranged."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="已出席", style=discord.ButtonStyle.success)
    async def attended_button(self, interaction: discord.Interaction, button: Button):
        """Handle Attended button click."""
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

    @discord.ui.button(label="未出席", style=discord.ButtonStyle.secondary)
    async def no_show_button(self, interaction: discord.Interaction, button: Button):
        """Handle No Show button click."""
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

    @discord.ui.button(label="取消", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
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

    # Add fields to the embed
    fields = [
        ("申請識別碼", str(form_response.uuid)),
        ("姓名", form_response.name),
        ("電子郵件", form_response.email),
        ("申請組別", ", ".join(form_response.interested_fields)),
    ]

    for name, value in fields:
        if value:
            value = truncate(str(value))
            embed.add_field(name=name, value=value, inline=False)

    view = InterviewResultView(form_response)
    await channel.send(embed=embed, view=view)


class InterviewResultView(View):
    """View for Stage 5: Interview Result."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="面試通過", style=discord.ButtonStyle.success)
    async def pass_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Passed button click."""
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

    @discord.ui.button(label="面試失敗", style=discord.ButtonStyle.danger)
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="轉接至他組", style=discord.ButtonStyle.secondary)
    async def transfer_button(self, interaction: discord.Interaction, button: Button):
        """Handle Transfer to Another Team button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        modal = TransferToTeamModal(self.form_response)
        await interaction.response.send_modal(modal)


class ManagerFillFormView(View):
    """View for Stage 6: Manager Fills in Information."""

    def __init__(self, form_response: FormResponse):
        super().__init__()
        self.form_response = form_response

    @discord.ui.button(label="填寫資料", style=discord.ButtonStyle.primary)
    async def fill_form_button(self, interaction: discord.Interaction, button: Button):
        """Handle Fill Form button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal for manager to fill in information
        modal = ManagerFillInfoModal1(self.form_response)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="取消", style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(self.form_response, action="取消")
        await interaction.response.send_modal(modal)
