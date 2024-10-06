# app/discord/application_process/modals.py
import discord
from discord.ui import Modal, TextInput

from app.models.form_response import FormResponse, InterviewStatus
from app.models.staff import Staff
from app.utils.redis_client import redis_client

from .helpers import get_bot, send_log_message, get_embed_color, truncate
from datetime import datetime


class FailureReasonModal(Modal):
    """Modal to input failure or cancellation reason."""

    def __init__(self, form_response: FormResponse, action: str):
        super().__init__(title="請填寫原因")
        self.form_response = form_response
        self.action = action  # '取消' 或 '面試失敗'
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
        history_entry = f"{now_str} --- {self.action} by {interaction.user.name}: {reason}"

        if not self.form_response.history:
            self.form_response.history = []
        self.form_response.history.append(history_entry)

        # Update status based on action
        if self.action == "取消":
            self.form_response.interview_status = InterviewStatus.CANCELLED
        elif self.action == "面試失敗":
            self.form_response.interview_status = InterviewStatus.INTERVIEW_FAILED

        self.form_response.save()

        # Edit the embed to include the reason and disable buttons
        embed = interaction.message.embeds[0]
        embed.title = f"申請已{self.action}"
        embed.color = get_embed_color(self.form_response.interview_status)
        embed.add_field(name=f"{self.action}原因", value=reason, inline=False)
        embed.add_field(name="歷史紀錄", value="\n".join(self.form_response.history), inline=False)
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"已更新{self.action}原因。", ephemeral=True)

        # Send log message
        await send_log_message(self.form_response, f"申請已{self.action}")


class TransferToTeamModal(Modal):
    """Modal to input the team to transfer to."""

    def __init__(self, form_response: FormResponse):
        super().__init__(title="轉接至他組")
        self.form_response = form_response
        self.team_input = TextInput(
            label="新的組別",
            required=True,
            placeholder="請輸入要轉接的組別",
        )
        self.manager_id_input = TextInput(
            label="新負責人Discord ID（可選）",
            required=False,
            placeholder="請輸入新負責人的Discord ID（可選）",
        )
        self.add_item(self.team_input)
        self.add_item(self.manager_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        # Verify identity
        if not is_authorized(interaction.user, self.form_response):
            await interaction.response.send_message("你無權執行此操作。", ephemeral=True)
            return

        # Update the form_response with the new team
        new_team = self.team_input.value
        new_manager_discord_id = self.manager_id_input.value.strip()

        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 轉接至 {new_team} by {interaction.user.name}"

        self.form_response.interested_fields = [new_team]

        if new_manager_discord_id:
            # Update manager_id
            staff = Staff.objects(discord_user_id=new_manager_discord_id).first()
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
        await interaction.message.delete()
        # Start over
        from .views import send_stage_embed

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
        # Store data in redis or in-memory
        redis_client.set(
            f"manager_fill:{self.form_response.uuid}",
            {
                "name": self.name_input.value,
                "email": self.email_input.value,
                "phone_number": self.phone_input.value,
                "high_school_stage": self.high_school_stage_input.value,
                "city": self.city_input.value,
            },
        )

        # Proceed to next modal
        modal = ManagerFillInfoModal2(self.form_response)
        await interaction.response.send_modal(modal)


class ManagerFillInfoModal2(Modal):
    """Second part of the manager's info modal."""

    def __init__(self, form_response: FormResponse):
        super().__init__(title="負責人填寫資料（2/2）")
        self.form_response = form_response

        self.current_group_input = TextInput(
            label="組別",
            placeholder="請輸入組別",
            required=True,
        )
        self.current_position_input = TextInput(
            label="身份",
            placeholder="請輸入身份",
            required=True,
        )

        self.add_item(self.current_group_input)
        self.add_item(self.current_position_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        # Retrieve data from redis or in-memory
        stored_data = redis_client.get(f"manager_fill:{self.form_response.uuid}")
        if not stored_data:
            await interaction.response.send_message("發生錯誤，請重新開始。", ephemeral=True)
            return

        # Create Staff model
        staff = Staff(
            name=stored_data["name"],
            email=stored_data["email"],
            phone_number=stored_data["phone_number"],
            high_school_stage=stored_data["high_school_stage"],
            city=stored_data["city"],
            current_group=self.current_group_input.value,
            current_position=self.current_position_input.value,
            discord_user_id=str(self.form_response.uuid),  # Placeholder, update accordingly
            is_signup=False,
        )
        staff.save()

        self.form_response.interview_status = InterviewStatus.INTERVIEW_PASSED_WAITING_FOR_FORM
        now_str = datetime.utcnow().strftime("%Y/%m/%d %H:%M")
        history_entry = f"{now_str} --- 負責人已填寫資料 by {interaction.user.name}"

        self.form_response.history.append(history_entry)
        self.form_response.save()

        await interaction.response.send_message("資料已填寫，等待申請者填寫剩餘資訊。", ephemeral=True)
        await interaction.message.delete()
        from .views import send_stage_embed

        await send_stage_embed(self.form_response, interaction.user)


def is_authorized(user, form_response):
    """Check if the user is authorized to perform actions on this form."""
    discord_user_id = str(user.id)
    staff = Staff.objects(discord_user_id=discord_user_id).first()
    if not staff:
        return False

    if str(staff.uuid) == form_response.manager_id or staff.permission_level >= 3:
        return True
    return False
