# app/discord/import_existing_members/views.py
import discord
from discord.ui import Button, Select, View

from .helpers import get_user_data, has_submitted_form, set_user_data
from .modals import (
    ExistingMemberContactInfoModal,
    ExistingMemberInfoCollectionModal1,
    ExistingMemberInfoCollectionModal2,
    ExistingMemberJobInfoCollectionModal,
)


class ProceedToInfoPart2View(View):
    """View to proceed to the next part of information collection."""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="繼續填寫資訊", style=discord.ButtonStyle.primary)
    async def proceed_button(self, interaction: discord.Interaction, button: Button):
        """Handle button click to proceed."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        modal = ExistingMemberInfoCollectionModal2(self.user_id)
        await interaction.response.send_modal(modal)


class ProceedToContactInfoView(View):
    """View to proceed to contact information collection."""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="繼續填寫聯絡資訊", style=discord.ButtonStyle.primary)
    async def proceed_button(self, interaction: discord.Interaction, button: Button):
        """Handle button click to proceed."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        modal = ExistingMemberContactInfoModal(self.user_id)
        await interaction.response.send_modal(modal)


class ExistingMemberJobInfoSelectView(View):
    """View to select job information."""

    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="選擇您的組別",
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
    async def select_callback(
        self, interaction: discord.Interaction, select: Select
    ):
        """Handle selection of job group."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        user_data = get_user_data(self.user_id)
        user_data["current_group"] = select.values[0]
        set_user_data(self.user_id, user_data)

        modal = ExistingMemberJobInfoCollectionModal(self.user_id)
        await interaction.response.send_modal(modal)


class CollectExistingMemberInfoView(View):
    """View to start collecting existing member information."""

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="開始填寫表單", style=discord.ButtonStyle.primary)
    async def collect_info(self, interaction: discord.Interaction, button: Button):
        """Handle button click to start information collection."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        modal = ExistingMemberInfoCollectionModal1(self.user_id)
        await interaction.response.send_modal(modal)
