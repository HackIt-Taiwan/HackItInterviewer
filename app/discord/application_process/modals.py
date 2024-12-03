# app/discord/application_process/modals.py
import discord
from discord.ui import Modal, TextInput

from .helpers import APPLY_LOG_CHANNEL_ID, send_log_message
from app.utils.mail_sender import send_email
from app.utils.db import get_staff


class FailureReasonModal(Modal):
    """Modal to input failure or cancellation reason."""

    def __init__(self, form_response, action: str):
        super().__init__(title="請填寫原因")
        self.form_response = form_response
        self.action = action  # 'cancel' or 'fail'
        self.reason_input = TextInput(
            label="原因",
            style=discord.TextStyle.long,
            required=True,
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            """Handle modal submission."""

            # Verify identity
            discord_user_id = str(interaction.user.id)
            payload = {"discord_id": discord_user_id}

            is_valid, staff = get_staff(payload)
            if not is_valid or staff.json().get("data")[0].get("permission_level") < 2:
                await interaction.response.send_message(
                    "你無權執行此操作。", ephemeral=True
                )
                return

            # Update the form_response with the reason
            reason = self.reason_input.value

            # Send email
            send_email(
                subject="HackIt / 招募結果通知",
                recipient=self.form_response.get("email"),
                template="emails/notification_fail.html",
                name=self.form_response.get("real_name"),
                uuid=self.form_response.get("uuid"),
                reason=reason,
            )

            await interaction.message.delete()
            await interaction.response.send_message(
                f"已完成{self.action}標記（存放於 <#{APPLY_LOG_CHANNEL_ID}>）。",
                ephemeral=True,
            )

            # Send log message
            await send_log_message(
                self.form_response, interaction.user, action=self.action, reason=reason
            )

            # btw, shouldn't we delete staff?
        except TypeError:
            await interaction.response.send_message(
                "錯誤，交互者或申請者不再資料庫內", ephemeral=True
            )
