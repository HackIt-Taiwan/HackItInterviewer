# app/discord/application_process/views.py
import time
import discord
from discord.ui import Button, View


from .modals import FailureReasonModal
from .helpers import send_stage_embed
from app.utils.mail_sender import send_email
from app.utils.jwt import generate_next_url
from app.utils.db import get_staff, update_staff


class FindMyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="查找負責案件",
        style=discord.ButtonStyle.primary,
        custom_id="find_my_applicants",
    )
    async def find_my_button(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle the button interaction to trigger the find-my logic."""
            if button.custom_id != "find_my_applicants":
                return

            await interaction.response.defer()
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}
            is_valid, staff = get_staff(payload)
            if (
                not is_valid
                or (staff.json().get("data") is None)
                or staff.json().get("data")[0].get("permission_level") < 2
            ):
                await interaction.followup.send("你無權執行此操作。", ephemeral=True)
                return

            payload = {"team_leader": discord_user_id}
            is_valid, applicants = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message(
                    "資料庫未知錯誤", ephemeral=True
                )

            if applicants is None:
                await interaction.followup.send("你目前沒有受理的申請者よ")

            applicants = applicants.json().get("data")
            embed_title = "你受理的申請者:"
            embed = discord.Embed(
                title=embed_title,
                color=0xFF4500,
            )
            embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")

            for applicant in applicants:
                link = applicant.get("apply_message")
                embed.add_field(name="連結:", value=link, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

    @discord.ui.button(
        label="查找未受理案件",
        style=discord.ButtonStyle.primary,
        custom_id="find_no_assignee_applicant",
    )
    async def find_no_assignee_button(
        self, interaction: discord.Interaction, button: Button
    ):
        try:
            """Handle the button interaction to trigger the find-my logic."""
            if button.custom_id != "find_no_assignee_applicant":
                return

            await interaction.response.defer()
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}
            is_valid, staff = get_staff(payload)
            if (
                not is_valid
                or (staff.json().get("data") is None)
                or staff.json().get("data")[0].get("permission_level") < 2
            ):
                await interaction.followup.send("你無權執行此操作。", ephemeral=True)
                return

            payload = {"team_leader": "0"}
            is_valid, applicants = get_staff(payload)
            if not is_valid:
                await interaction.response.send_message(
                    "資料庫未知錯誤", ephemeral=True
                )

            if applicants is None:
                await interaction.followup.send("目前沒有未受理申請者", ephemeral=True)

            applicants = applicants.json().get("data")
            embed_title = "未受理的申請者:"
            embed = discord.Embed(
                title=embed_title,
                color=0xFF4500,
            )
            embed.set_footer(text=time.strftime("%Y/%m/%d %H:%M") + " ● HackIt")

            for applicant in applicants:
                link = applicant.get("apply_message")
                embed.add_field(name="連結:", value=link, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )


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
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

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
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )


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

            # Delete applicant's assignee
            payload = {
                "team_leader": "",
                "apply_message": "",
            }
            update_staff(applicant.get("uuid"), payload)
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

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
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

    @discord.ui.button(
        label="轉移組別",
        style=discord.ButtonStyle.danger,
        custom_id="change_group",
    )
    async def change_group(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle group changing button"""
            if button.custom_id != "change_group":
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

            await interaction.response.send_message("test")
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

    @discord.ui.button(
        label="更換受理人",
        style=discord.ButtonStyle.danger,
        custom_id="change_assignee",
    )
    async def change_assignee(self, interaction: discord.Interaction, button: Button):
        try:
            """Handle assignee chagning button (so you can blame others)"""
            if button.custom_id != "change_assignee":
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

            await interaction.response.send_message("test")
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )

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

            # Get applicant info, yes I wrote this 5 times because of circular import problem.
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
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )
