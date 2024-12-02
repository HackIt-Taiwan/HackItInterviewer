# app/discord/application_process/views.py
import discord
from discord.ui import Button, View


from .modals import FailureReasonModal
from .helpers import send_stage_embed
from app.utils.db import get_staff
from app.utils.mail_sender import send_email
from app.utils.jwt import generate_next_url


class FormResponseView(View):
    """Base View that handles form_response retrieval."""

    def __init__(self):
        super().__init__(timeout=None)


class AcceptOrCancelView(FormResponseView):
    """View with Accept and Cancel buttons for Stage 1."""

    def __init__(self):
        super().__init__()

    @discord.ui.button(
        label="受理",
        style=discord.ButtonStyle.success,
        custom_id="accept_or_cancel_view_accept",
    )
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle Accept button click."""
            if button.custom_id != "accept_or_cancel_view_accept":
                return

            # Get applicant info
            message = interaction.message
            if not message.embeds:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return
            embed = message.embeds[0]

            uuid = None
            for field in embed.fields:
                if field.name == "申請識別碼":
                    uuid = field.value
                    break

            payload = {"uuid": uuid}
            is_valid, applicant = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return

            applicant = applicant.json().get("data")[0]

            # Check permission level of the user who pressed it
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            # Proceed to next stage
            await interaction.response.send_message(
                "已受理，進入下一階段。", ephemeral=True
            )
            await interaction.message.delete()

            # Send embed
            await send_stage_embed(applicant, interaction.user)
        except TypeError:
            await interaction.response.send_message("錯誤，交互者或申請者不再資料庫內")

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="accept_or_cancel_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle Cancel button click."""
            if button.custom_id != "accept_or_cancel_view_cancel":
                return

            # Get applicant info
            message = interaction.message
            if not message.embeds:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return
            embed = message.embeds[0]

            uuid = None
            for field in embed.fields:
                if field.name == "申請識別碼":
                    uuid = field.value
                    break

            payload = {"uuid": uuid}
            is_valid, applicant = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return

            applicant = applicant.json().get("data")[0]

            # Identity verification
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            # Open modal to input cancellation reason
            modal = FailureReasonModal(applicant, action="NOT_ACCEPTED")
            await interaction.response.send_modal(modal)
        except TypeError:
            await interaction.response.send_message("錯誤，交互者或申請者不再資料庫內")


class InterviewResultView(FormResponseView):
    """View for Stage 2: Interview Result."""

    @discord.ui.button(
        label="面試通過",
        style=discord.ButtonStyle.success,
        custom_id="interview_result_view_pass",
    )
    async def pass_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle Interview Passed button click."""
            if button.custom_id != "interview_result_view_pass":
                return

            # Get applicant info
            message = interaction.message
            if not message.embeds:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return
            embed = message.embeds[0]

            uuid = None
            for field in embed.fields:
                if field.name == "申請識別碼":
                    uuid = field.value
                    break

            payload = {"uuid": uuid}
            is_valid, applicant = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return

            applicant = applicant.json().get("data")[0]

            # Identity verification
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            next_url = generate_next_url(applicant.get("uuid"))

            send_email(
                subject="Counterspell / 招募結果通知",
                recipient=applicant.get("email"),
                template="emails/notification_pass.html",
                name=applicant.get("real_name"),
                uuid=applicant.get("uuid"),
                next_url=next_url,
            )

            await interaction.response.send_message(
                "面試通過，已傳送第二部分表單給申請者。", ephemeral=True
            )
            await interaction.message.delete()

            # Send log message
            from .helpers import send_log_message

            await send_log_message(
                applicant,
                interaction.user,
                action="INTERVIEW_PASSED",
            )
        except TypeError:
            await interaction.response.send_message("錯誤，交互者或申請者不再資料庫內")

    @discord.ui.button(
        label="面試失敗",
        style=discord.ButtonStyle.danger,
        custom_id="interview_result_view_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle Interview Failed button click."""
            if button.custom_id != "interview_result_view_fail":
                return

            # Get applicant info
            message = interaction.message
            if not message.embeds:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return
            embed = message.embeds[0]

            uuid = None
            for field in embed.fields:
                if field.name == "申請識別碼":
                    uuid = field.value
                    break

            payload = {"uuid": uuid}
            is_valid, applicant = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return

            applicant = applicant.json().get("data")[0]

            # Identity verification
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            modal = FailureReasonModal(applicant, action="INTERVIEW_FAILED")
            await interaction.response.send_modal(modal)
        except TypeError:
            await interaction.response.send_message("錯誤，交互者或申請者不再資料庫內")

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="interview_result_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle Cancel button click."""
            if button.custom_id != "interview_result_view_cancel":
                return

            # Get applicant info
            message = interaction.message
            if not message.embeds:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return
            embed = message.embeds[0]

            uuid = None
            for field in embed.fields:
                if field.name == "申請識別碼":
                    uuid = field.value
                    break

            payload = {"uuid": uuid}
            is_valid, applicant = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message("未知錯誤", ephemeral=True)
                return

            applicant = applicant.json().get("data")[0]

            # Identity verification
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            # Open modal to input cancellation reason
            modal = FailureReasonModal(applicant, action="INTERVIEW_CANCELLED")
            await interaction.response.send_modal(modal)
        except TypeError:
            await interaction.response.send_message("錯誤，交互者或申請者不再資料庫內")
