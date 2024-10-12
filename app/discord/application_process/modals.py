# app/discord/application_process/modals.py
import discord
from discord.ui import Modal, TextInput, View, Select, Button, UserSelect
import json
from datetime import datetime

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff
from app.utils.redis_client import redis_client

from .helpers import (
    is_authorized,
    get_embed_color,
    send_log_message,
    send_stage_embed, APPLY_LOG_CHANNEL_ID,
)
from ...utils.encryption import hash_data
from ...utils.mail_sender import send_email


class FailureReasonModal(Modal):
    """Modal to input failure or cancellation reason."""

    def __init__(self, form_response: FormResponse, action: str):
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
        """Handle modal submission."""
        # Verify identity
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Update the form_response with the reason
        reason = self.reason_input.value
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- {self.action} by {interaction.user.name}"

        if not self.form_response.history:
            self.form_response.history = []
        self.form_response.history.append(history_entry)

        # Update status based on action
        if self.action == "取消":
            self.form_response.interview_status = InterviewStatus.CANCELLED
        elif self.action == "面試失敗":
            self.form_response.interview_status = InterviewStatus.INTERVIEW_FAILED

        self.form_response.save()

        await interaction.message.delete()
        await interaction.response.send_message(f"已完成{self.action}標記（存放於 <#{APPLY_LOG_CHANNEL_ID}>）。", ephemeral=True)

        # Send log message
        await send_log_message(self.form_response, f"申請已標註{self.action}", reason=reason)


class TransferToTeamView(View):
    """View to select the new team and new manager."""

    def __init__(self, form_response):
        super().__init__(timeout=None)
        self.form_response = form_response
        self.new_team = None
        self.new_manager = None

    @discord.ui.select(
        placeholder="選擇新的組別",
        options=[
            discord.SelectOption(label="HackIt", value="HackIt"),
            discord.SelectOption(label="策劃部", value="策劃部"),
            discord.SelectOption(label="設計部", value="設計部"),
            discord.SelectOption(label="行政部", value="行政部"),
            discord.SelectOption(label="公關組", value="公關組"),
            discord.SelectOption(label="活動企劃組", value="活動企劃組"),
            discord.SelectOption(label="美術組", value="美術組"),
            discord.SelectOption(label="資訊組", value="資訊組"),
            discord.SelectOption(label="影音組", value="影音組"),
            discord.SelectOption(label="行政組", value="行政組"),
            discord.SelectOption(label="財務組", value="財務組"),
            discord.SelectOption(label="其他", value="其他"),
        ],
    )
    async def team_select(self, interaction: discord.Interaction, select: Select):
        self.new_team = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        cls=UserSelect,
        placeholder="選擇新的負責人",
        min_values=1,
        max_values=1,
        custom_id="manager_select",
    )
    async def manager_select(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        self.new_manager = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(
        label="確認轉接",
        style=discord.ButtonStyle.success,
        custom_id="transfer_to_team_view_confirm",
    )
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        """Handle Confirm button click."""
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        if not self.new_team or not self.new_manager:
            await interaction.response.send_message("請選擇新的組別和新的負責人。", ephemeral=True)
            return

        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 轉接至 {self.new_team} by {interaction.user.name}"

        # Update manager_id
        staff = Staff.objects(discord_user_id=str(self.new_manager.id)).first()
        if staff:
            self.form_response.manager_id = str(staff.uuid)
            history_entry += f", 新負責人: {staff.name}"
        else:
            await interaction.response.send_message("未找到該Discord ID的負責人。", ephemeral=True)
            return

        self.form_response.history.append(history_entry)
        self.form_response.interview_status = InterviewStatus.NOT_CONTACTED
        self.form_response.save()

        await interaction.response.send_message("已轉接至他組，流程重新開始。", ephemeral=True)
        await send_stage_embed(self.form_response, interaction.user)


class ManagerFillInfoModal1(Modal):
    """First part of the manager's info modal."""

    def __init__(self, form_response: FormResponse):
        super().__init__(title="負責人填寫資料（1/2）")
        self.form_response = form_response

        # Pre-fill with existing data
        self.name_input = TextInput(
            label="姓名",
            default=form_response.name,
            required=True,
        )
        self.email_input = TextInput(
            label="電子郵件",
            default=form_response.email,
            required=True,
        )
        self.phone_input = TextInput(
            label="電話號碼",
            default=form_response.phone_number,
            required=True,
        )
        self.high_school_stage_input = TextInput(
            label="高中階段",
            default=form_response.high_school_stage,
            required=True,
        )
        self.city_input = TextInput(
            label="城市",
            default=form_response.city,
            required=True,
        )

        self.add_item(self.name_input)
        self.add_item(self.email_input)
        self.add_item(self.phone_input)
        self.add_item(self.high_school_stage_input)
        self.add_item(self.city_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        # Store data in redis
        redis_client.set(
            f"manager_fill:{self.form_response.uuid}",
            json.dumps({
                "name": self.name_input.value,
                "email": self.email_input.value,
                "phone_number": self.phone_input.value,
                "high_school_stage": self.high_school_stage_input.value,
                "city": self.city_input.value,
            }),
            ex=86400  # Set an expiration time (optional)
        )

        embed = discord.Embed(
            title="請選擇組員組別",
            description="請選擇要賦予的組別。\n請立即完成此動作，否則資料將被清除。",
            color=0x3498DB,
        )

        view = ManagerFillInfoModal2(self.form_response)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await interaction.message.delete()




class ManagerFillInfoModal2(View):
    """View to select job information."""

    def __init__(self, form_response):
        super().__init__(timeout=600)
        self.form_response = form_response

    @discord.ui.select(
        placeholder="選擇賦予的組別",
        options=[
            discord.SelectOption(label="HackIt", value="HackIt"),
            discord.SelectOption(label="策劃部", value="策劃部"),
            discord.SelectOption(label="設計部", value="設計部"),
            discord.SelectOption(label="行政部", value="行政部"),
            discord.SelectOption(label="公關組", value="公關組"),
            discord.SelectOption(label="活動企劃組", value="活動企劃組"),
            discord.SelectOption(label="美術組", value="美術組"),
            discord.SelectOption(label="資訊組", value="資訊組"),
            discord.SelectOption(label="影音組", value="影音組"),
            discord.SelectOption(label="行政組", value="行政組"),
            discord.SelectOption(label="財務組", value="財務組"),
            discord.SelectOption(label="其他", value="其他"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        # Retrieve data from redis
        stored_data = redis_client.get(f"manager_fill:{self.form_response.uuid}")
        if not stored_data:
            await interaction.response.send_message("發生錯誤。（超時或已填寫完成）", ephemeral=True)
            return

        stored_data = json.loads(stored_data)

        # Create Staff model
        staff = Staff(
            name=stored_data["name"],
            email=stored_data["email"],
            email_hash=hash_data(stored_data["email"]),
            phone_number=stored_data["phone_number"],
            high_school_stage=stored_data["high_school_stage"],
            city=stored_data["city"],
            current_group=select.values[0],
            current_position="組員",
            is_signup=False,
        )
        staff.save()

        self.form_response.interview_status = InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 負責人已填寫資料 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        redis_client.delete(f"manager_fill:{self.form_response.uuid}")
        await interaction.response.send_message(f"資料填寫成功，已完成該成員面試相關事務！（<#{APPLY_LOG_CHANNEL_ID}>）", ephemeral=True)
        await send_log_message(self.form_response, "面試通過，已填寫資料", select.values[0])
