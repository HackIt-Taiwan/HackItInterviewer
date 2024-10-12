# app/discord/application_process/views.py
import io
import re
import time

import discord
from discord.ui import Button, View, UserSelect, Select
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
    ManagerFillInfoModal1,
    is_authorized, TransferToTeamView,
)


class FormResponseView(View):
    """Base View that handles form_response retrieval."""

    def __init__(self):
        super().__init__(timeout=None)

    async def get_form_response(self, interaction: discord.Interaction):
        """Retrieve form_response from the database using interaction.message.id."""
        last_message_id = str(interaction.message.id)
        form_response = FormResponse.objects(last_message_id=last_message_id).first()
        if not form_response:
            await interaction.response.send_message("表單資料未找到。", ephemeral=True)
            return None
        return form_response



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

        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        # Check permission level of the user
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Update form_response
        form_response.manager_id = str(staff.uuid)
        form_response.interview_status = InterviewStatus.NOT_CONTACTED
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 受理 by {interaction.user.name}"

        if not form_response.history:
            form_response.history = []
        form_response.history.append(history_entry)
        form_response.save()

        # Proceed to next stage
        await interaction.response.send_message("已受理，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(form_response, interaction.user)

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
        discord_user_id = str(interaction.user.id)
        staff = Staff.objects(discord_user_id=discord_user_id).first()
        if not staff or staff.permission_level < 2:
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal to input cancellation reason
        modal = FailureReasonModal(form_response, action="取消")
        await interaction.response.send_modal(modal)


def get_view_for_stage(form_response: FormResponse):
    """Return the appropriate view based on the current stage."""
    status = form_response.interview_status

    if status == InterviewStatus.NOT_CONTACTED:
        return ContactOrFailView()
    elif status == InterviewStatus.EMAIL_SENT:
        return ArrangeOrCancelView()
    elif status == InterviewStatus.INTERVIEW_SCHEDULED:
        return AttendOrNoShowView()
    elif status == InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM:
        return ManagerFillFormView()
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
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        # Check if the user is the manager
        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        form_response.is_email_contacted = True
        form_response.interview_status = InterviewStatus.EMAIL_SENT
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 已聯繫 by {interaction.user.name}"

        form_response.history.append(history_entry)
        form_response.save()

        await interaction.response.send_message("已聯繫，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(form_response, interaction.user)

    @discord.ui.button(
        label="面試失敗",
        style=discord.ButtonStyle.danger,
        custom_id="contact_or_fail_view_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="已取消",
        style=discord.ButtonStyle.danger,
        custom_id="contact_or_fail_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="取消")
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
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        form_response.is_interview_scheduled = True
        form_response.interview_status = InterviewStatus.INTERVIEW_SCHEDULED
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 已安排面試 by {interaction.user.name}"

        form_response.history.append(history_entry)
        form_response.save()

        await interaction.response.send_message("已安排面試，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(form_response, interaction.user)

    @discord.ui.button(
        label="已取消",
        style=discord.ButtonStyle.danger,
        custom_id="arrange_or_cancel_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="取消")
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
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        form_response.is_attended_interview = True
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 面試已出席 by {interaction.user.name}"

        form_response.history.append(history_entry)
        form_response.save()

        # Proceed to next stage
        await interaction.response.send_message("面試已出席，進入下一階段。", ephemeral=True)
        await interaction.message.delete()
        # Send the interview result embed
        await send_interview_result_embed(form_response, interaction.user)

    @discord.ui.button(
        label="未出席",
        style=discord.ButtonStyle.secondary,
        custom_id="attend_or_no_show_view_no_show",
    )
    async def no_show_button(self, interaction: discord.Interaction, button: Button):
        """Handle No Show button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        form_response.interview_status = InterviewStatus.NO_SHOW
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 未出席面試 by {interaction.user.name}"

        form_response.history.append(history_entry)
        form_response.save()

        # Go back to Stage 3
        await interaction.response.send_message("未出席面試，返回安排面試階段。", ephemeral=True)
        await interaction.message.delete()
        form_response.interview_status = InterviewStatus.EMAIL_SENT
        await send_stage_embed(form_response, interaction.user)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="attend_or_no_show_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="取消")
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
        description=f"請選擇面試結果 cc:{user.mention}",
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

    view = InterviewResultView()
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
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        form_response.interview_status = InterviewStatus.INTERVIEW_PASSED_WAITING_MANAGER_FORM
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 面試通過 by {interaction.user.name}"

        form_response.history.append(history_entry)
        form_response.save()

        await interaction.response.send_message("面試通過，請填寫資料。", ephemeral=True)
        await interaction.message.delete()
        await send_stage_embed(form_response, interaction.user)

    @discord.ui.button(
        label="面試失敗",
        style=discord.ButtonStyle.danger,
        custom_id="interview_result_view_fail",
    )
    async def fail_button(self, interaction: discord.Interaction, button: Button):
        """Handle Interview Failed button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="面試失敗")
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="轉接至他組",
        style=discord.ButtonStyle.secondary,
        custom_id="interview_result_view_transfer",
    )
    async def transfer_button(self, interaction: discord.Interaction, button: Button):
        """Handle Transfer to Another Team button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        view = TransferToTeamView(form_response)
        embed = discord.Embed(
            title="轉接至他組",
            description="請選擇新的組別和新的負責人。\n請盡速選擇，否則資料將被清空。\n\n按鈕請勿重複使用！！！。",
            color=0x3498DB,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await interaction.message.delete()


class ManagerFillFormView(FormResponseView):
    """View for Stage 6: Manager Fills in Information."""

    @discord.ui.button(
        label="填寫資料",
        style=discord.ButtonStyle.primary,
        custom_id="manager_fill_form_view_fill_form",
    )
    async def fill_form_button(self, interaction: discord.Interaction, button: Button):
        """Handle Fill Form button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Open modal for manager to fill in information
        modal = ManagerFillInfoModal1(form_response)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="取消",
        style=discord.ButtonStyle.danger,
        custom_id="manager_fill_form_view_cancel",
    )
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Handle Cancel button click."""
        form_response = await self.get_form_response(interaction)
        if not form_response:
            return

        if not is_authorized(interaction.user, form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return
        modal = FailureReasonModal(form_response, action="取消")
        await interaction.response.send_modal(modal)

class FindMyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="查找負責案件", style=discord.ButtonStyle.primary, custom_id="find_my_button")
    async def find_my_button(self, interaction: discord.Interaction, button: Button):
        """Handle the button interaction to trigger the find-my logic."""
        if button.custom_id != "find_my_button":
            return

        await interaction.response.defer()
        staff_member = Staff.objects(discord_user_id=str(interaction.user.id)).first()
        if staff_member is None:
            no_staff_embed = discord.Embed(description=f"使用者 {interaction.user.mention} 越權查詢！", color=0xff6666)
            await interaction.followup.send(embed=no_staff_embed, ephemeral=True)
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
            await interaction.followup.send(embed=no_cases_embed, ephemeral=True)
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
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="查找未受理案件", style=discord.ButtonStyle.secondary, custom_id="find_not_accepted_button")
    async def find_not_accepted_button(self, interaction: discord.Interaction, button: Button):
        """Handle the button interaction to find all NOT_ACCEPTED cases."""
        if button.custom_id != "find_not_accepted_button":
            return

        await interaction.response.defer()
        not_accepted_apps = FormResponse.objects(interview_status=InterviewStatus.NOT_ACCEPTED)

        if not not_accepted_apps:
            no_cases_embed = discord.Embed(description="目前沒有未受理的案件。", color=0xff6666)
            await interaction.followup.send(embed=no_cases_embed, ephemeral=True)
            return

        embeds = []
        description = ""
        max_length = 1024 - 80  # Adjust as needed

        for app in not_accepted_apps:
            # Construct the message link if available
            if app.last_message_id:
                message_link = f"https://discord.com/channels/{interaction.guild.id}/{APPLY_FORM_CHANNEL_ID}/{app.last_message_id}"
                message_jump = f"[跳轉到訊息]({message_link})"
            else:
                message_jump = "無法取得訊息連結"

            line = f"{app.name} -- {app.email} \n {', '.join(app.interested_fields)} / {message_jump}\n\n"
            if len(description) + len(line) > max_length:
                embed = discord.Embed(description=description, color=0x3498DB)
                embeds.append(embed)
                description = ""
            description += line

        if description:
            embed = discord.Embed(description=description, color=0x3498DB)
            embeds.append(embed)

        # Send the embeds
        for embed in embeds:
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="查找案件 (過濾版)", style=discord.ButtonStyle.secondary, custom_id="find_cases_filtered_button")
    async def find_cases_filtered_button(self, interaction: discord.Interaction, button: Button):
        """Handle the button interaction to find cases with filters."""
        if button.custom_id != "find_cases_filtered_button":
            return

        # Create the FilterCasesView and send it to the user
        view = FilterCasesView()
        embed = discord.Embed(
            title="查找案件（過濾版）",
            description="請選擇過濾條件（至少選擇一個）。",
            color=0x3498DB,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class FilterCasesView(View):
    """View to filter and find cases based on selected criteria."""

    def __init__(self):
        super().__init__(timeout=600)
        self.status = None
        self.interested_field = None
        self.manager = None

        # Status Select
        self.status_select = Select(
            placeholder="選擇案件狀態（可選）",
            options=[
                discord.SelectOption(label="未受理", value="NOT_ACCEPTED"),
                discord.SelectOption(label="受理中", value="IN_PROGRESS"),
                discord.SelectOption(label="面試完成", value="COMPLETED"),
            ],
            min_values=0, max_values=1,
            custom_id="status_select"
        )
        self.status_select.callback = self.status_select_callback
        self.add_item(self.status_select)

        # Interested Field Select
        self.interested_field_select = Select(
            placeholder="選擇組別（可選）",
            options=[
                discord.SelectOption(label="公關組", value="公關組"),
                discord.SelectOption(label="活動企劃組", value="活動企劃組"),
                discord.SelectOption(label="美術組", value="美術組"),
                discord.SelectOption(label="資訊組", value="資訊組"),
                discord.SelectOption(label="影音組", value="影音組"),
                discord.SelectOption(label="行政組", value="行政組"),
                discord.SelectOption(label="財務組", value="財務組"),
            ],
            min_values=0, max_values=1,
            custom_id="interested_field_select"
        )
        self.interested_field_select.callback = self.interested_field_select_callback
        self.add_item(self.interested_field_select)

        # Manager UserSelect
        self.manager_select = UserSelect(
            placeholder="選擇負責人（可選）",
            min_values=0,
            max_values=1,
            custom_id="manager_select"
        )
        self.manager_select.callback = self.manager_select_callback
        self.add_item(self.manager_select)

        # Add Search and Cancel buttons
        self.search_button = Button(
            label="搜尋",
            style=discord.ButtonStyle.success,
            custom_id="filter_cases_search_button"
        )
        self.search_button.callback = self.search_button_callback
        self.add_item(self.search_button)

    async def status_select_callback(self, interaction: discord.Interaction):
        self.status = self.status_select.values[0] if self.status_select.values else None
        await interaction.response.defer()

    async def interested_field_select_callback(self, interaction: discord.Interaction):
        self.interested_field = self.interested_field_select.values[0] if self.interested_field_select.values else None
        await interaction.response.defer()

    async def manager_select_callback(self, interaction: discord.Interaction):
        if self.manager_select.values:
            self.manager = self.manager_select.values[0]
        else:
            self.manager = None
        await interaction.response.defer()

    async def search_button_callback(self, interaction: discord.Interaction):
        # Defer the interaction, since we're going to send follow-up messages
        await interaction.response.defer(ephemeral=True)

        # Handle the search logic
        if not self.status and not self.interested_field and not self.manager:
            await interaction.followup.send("請至少選擇一個過濾條件。", ephemeral=True)
            return

        # Build the query
        query = {}
        if self.status:
            if self.status == "NOT_ACCEPTED":
                query['interview_status'] = InterviewStatus.NOT_ACCEPTED
            elif self.status == "IN_PROGRESS":
                # Exclude 'NOT_ACCEPTED' and 'COMPLETED' statuses
                completed_statuses = [
                    InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM,
                    InterviewStatus.INTERVIEW_PASSED,
                    InterviewStatus.CANCELLED,
                    InterviewStatus.INTERVIEW_FAILED,
                ]
                query['interview_status__nin'] = [InterviewStatus.NOT_ACCEPTED] + completed_statuses
            elif self.status == "COMPLETED":
                query['interview_status__in'] = [
                    InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM,
                    InterviewStatus.INTERVIEW_PASSED,
                    InterviewStatus.CANCELLED,
                    InterviewStatus.INTERVIEW_FAILED,
                ]

        if self.interested_field:
            query['interested_fields__contains'] = self.interested_field

        if self.manager:
            manager_staff = Staff.objects(discord_user_id=str(self.manager.id)).first()
            if manager_staff:
                query['manager_id'] = str(manager_staff.uuid)
            else:
                await interaction.followup.send("未找到該負責人的資料。", ephemeral=True)
                return

        # Query the database
        apps = FormResponse.objects(**query)

        if not apps:
            no_cases_embed = discord.Embed(description="目前沒有符合條件的案件。", color=0xff6666)
            await interaction.followup.send(embed=no_cases_embed, ephemeral=True)
            return

        # Prepare the results
        embeds = []
        description = ""
        max_length = 1024 - 80  # Adjust as needed

        for app in apps:
            # Construct the message link if available
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
            embed = discord.Embed(description=description, color=0x3498DB)
            embeds.append(embed)

        # Send the embeds
        for embed in embeds:
            await interaction.followup.send(embed=embed, ephemeral=True)

