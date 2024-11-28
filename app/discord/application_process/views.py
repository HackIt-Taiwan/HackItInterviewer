# app/discord/application_process/views.py
import os
import time
import requests

import discord
from discord.ui import Button, View, UserSelect, Select
from datetime import datetime


from .helpers import (
    truncate,
    get_bot,
    get_embed_color,
    APPLY_FORM_CHANNEL_ID,
    # send_stage_embed,
)
# from .modals import (
    # FailureReasonModal,
    # is_authorized,
# )


class AcceptOrCancelView:
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

        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        # Check permission level of the user
        discord_user_id = str(interaction.user.id)
        payload = {"discord_id": discord_user_id}
        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}
        staff = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/getstaffs",
            headers=headers,
            json=payload,
        )
        staff = staff.json().get("data")[0]
        if not staff or staff.get("permission_level") < 2:
            await interaction.response.send_message(
                "你無權執行此操作。", ephemeral=True
            )
            return

        # Update form_response
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 受理 by {interaction.user.name}"

        # Proceed to next stage
        await interaction.response.send_message(
            "已受理，進入下一階段。", ephemeral=True
        )
        await interaction.message.delete()
        # await send_stage_embed(form_response, interaction.user)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="accept_or_cancel_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        if button.custom_id != "accept_or_cancel_view_cancel":
            return

        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        # Identity verification
        # CHANGE THIS get staff here with backend
        discord_user_id = str(interaction.user.id)
        payload = {"discord_id": discord_user_id}
        headers = {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', '')}"}
        staff = requests.post(
            url=f"{os.getenv("BACKEND_ENDPOINT")}/staff/getstaffs",
            headers=headers,
            json=payload,
        )
        staff = staff.json().get("data")[0]
        if not staff or staff.get("permission_level") < 2:
            await interaction.response.send_message(
                "你無權執行此操作。", ephemeral=True
            )
            return

        # Open modal to input cancellation reason
        # modal = FailureReasonModal(form_response, action="取消")
        # await interaction.response.send_modal(modal)


# class InterviewResultView:
#     """View for Stage 2: Interview Result."""
#
#     @discord.ui.button(
#         label="面試通過",
#         style=discord.ButtonStyle.success,
#         custom_id="interview_result_view_pass",
#     )
#     async def pass_button(self, interaction: discord.Interaction, button: Button):
#         """Handle Interview Passed button click."""
#         form_response = await self.get_form_response(interaction)
#         if not form_response:
#             return
#
#         if not is_authorized(interaction.user, form_response):
#             await interaction.response.send_message(
#                 "你無權執行此操作。", ephemeral=True
#             )
#             return
#
#         form_response.interview_status = (
#             InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM
#         )
#         now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
#         history_entry = f"{now_str} --- 面試通過 by {interaction.user.name}"
#
#         form_response.history.append(history_entry)
#         form_response.save()
#
#         await interaction.response.send_message(
#             "面試通過，請填寫資料。", ephemeral=True
#         )
#         await interaction.message.delete()
#         await send_stage_embed(form_response, interaction.user)
#
#     @discord.ui.button(
#         label="面試失敗",
#         style=discord.ButtonStyle.danger,
#         custom_id="interview_result_view_fail",
#     )
#     async def fail_button(self, interaction: discord.Interaction, button: Button):
#         """Handle Interview Failed button click."""
#         form_response = await self.get_form_response(interaction)
#         if not form_response:
#             return
#
#         if not is_authorized(interaction.user, form_response):
#             await interaction.response.send_message(
#                 "你無權執行此操作。", ephemeral=True
#             )
#             return
#         modal = FailureReasonModal(form_response, action="面試失敗")
#         await interaction.response.send_modal(modal)
#
#     @discord.ui.button(
#         label="轉接至他組",
#         style=discord.ButtonStyle.secondary,
#         custom_id="interview_result_view_transfer",
#     )
#     async def transfer_button(self, interaction: discord.Interaction, button: Button):
#         """Handle Transfer to Another Team button click."""
#         form_response = await self.get_form_response(interaction)
#         if not form_response:
#             return
#
#         if not is_authorized(interaction.user, form_response):
#             await interaction.response.send_message(
#                 "你無權執行此操作。", ephemeral=True
#             )
#             return
#
#         view = TransferToTeamView(form_response)
#         embed = discord.Embed(
#             title="轉接至他組",
#             description="請選擇新的組別和新的負責人。\n請盡速選擇，否則資料將被清空。\n\n按鈕請勿重複使用！！！。",
#             color=0x3498DB,
#         )
#         await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
#         await interaction.message.delete()
