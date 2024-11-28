# app/discord/application_process/modals.py
# import discord
# from discord.ui import Modal, TextInput, View, Select, Button, UserSelect
# import json
# from datetime import datetime
#
# from app.models.form_response import FormResponse, InterviewStatus
# from app.models.staff import Staff
#
# from .helpers import (
#     is_authorized,
#     get_embed_color,
#     send_log_message,
#     send_stage_embed,
#     APPLY_LOG_CHANNEL_ID,
# )
# from ...utils.encryption import hash_data
# from ...utils.mail_sender import send_email
#
#
# class FailureReasonModal(Modal):
#     """Modal to input failure or cancellation reason."""
#
#     def __init__(self, form_response: FormResponse, action: str):
#         super().__init__(title="請填寫原因")
#         self.form_response = form_response
#         self.action = action  # 'cancel' or 'fail'
#         self.reason_input = TextInput(
#             label="原因",
#             style=discord.TextStyle.long,
#             required=True,
#         )
#         self.add_item(self.reason_input)
#
#     async def on_submit(self, interaction: discord.Interaction):
#         """Handle modal submission."""
#         # Verify identity
#         if not is_authorized(interaction.user, self.form_response):
#             await interaction.response.send_message(
#                 "你無權執行此操作。", ephemeral=True
#             )
#             return
#
#         # Update the form_response with the reason
#         reason = self.reason_input.value
#         now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
#         history_entry = f"{now_str} --- {self.action} by {interaction.user.name}"
#
#         if not self.form_response.history:
#             self.form_response.history = []
#         self.form_response.history.append(history_entry)
#
#         # Update status based on action
#         if self.action == "取消":
#             self.form_response.interview_status = InterviewStatus.CANCELLED
#         elif self.action == "面試失敗":
#             self.form_response.interview_status = InterviewStatus.INTERVIEW_FAILED
#
#         self.form_response.save()
#
#         await interaction.message.delete()
#         await interaction.response.send_message(
#             f"已完成{self.action}標記（存放於 <#{APPLY_LOG_CHANNEL_ID}>）。",
#             ephemeral=True,
#         )
#
#         # Send log message
#         await send_log_message(
#             self.form_response, f"申請已標註{self.action}", reason=reason
#         )
