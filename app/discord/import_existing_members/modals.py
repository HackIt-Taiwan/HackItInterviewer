# app/discord/import_existing_members/modals.py
import discord
from discord.ui import Modal, TextInput

from app.models.staff import EmergencyContact, Staff
from app.utils.redis_client import redis_client

from .helpers import (
    get_user_data,
    has_submitted_form,
    mark_form_as_submitted,
    set_user_data,
    truncate,
)


class ExistingMemberJobInfoCollectionModal(Modal):
    """Modal to collect job information from existing members."""

    def __init__(self, user_id):
        super().__init__(title="工作資訊")
        self.user_id = user_id
        self.add_item(
            TextInput(
                label="身份（如成員、負責人）",
                custom_id="current_position",
                required=True,
            )
        )
        self.add_item(
            TextInput(
                label="主要職責",
                custom_id="primary_role",
                required=False,
            )
        )
        self.add_item(
            TextInput(
                label="專長（用逗號分隔）",
                custom_id="expertise",
                required=False,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        user_data = get_user_data(self.user_id)
        user_data["current_position"] = self.children[0].value
        user_data["primary_role"] = self.children[1].value
        user_data["expertise"] = (
            [exp.strip() for exp in self.children[2].value.split(",")]
            if self.children[2].value
            else []
        )
        set_user_data(self.user_id, user_data)

        # Save data to Staff model
        emergency_contact_data = user_data.get("emergency_contact", {})
        emergency_contact = EmergencyContact(
            name=emergency_contact_data.get("name"),
            relationship=emergency_contact_data.get("relationship"),
            phone_number=emergency_contact_data.get("phone_number"),
        )

        staff = Staff(
            name=user_data["name"],
            nickname=user_data["nickname"],
            email=user_data["email"],
            email_hash=user_data["email_hash"],
            phone_number=user_data["phone"],
            high_school_stage=user_data["high_school_stage"],
            city=user_data["city"],
            school=user_data["school"],
            emergency_contact=emergency_contact,
            line_id=user_data.get("line_id"),
            ig_id=user_data.get("ig_id"),
            introduction=user_data.get("introduction"),
            current_group=user_data["current_group"],
            current_position=user_data["current_position"],
            primary_role=user_data.get("primary_role"),
            expertise=user_data.get("expertise"),
            discord_user_id=str(interaction.user.id),
            is_signup=True,  # Automatically set to True
        )
        staff.save()

        # Mark the form as submitted without expiration
        mark_form_as_submitted(self.user_id)
        redis_client.delete(f"user_data:{self.user_id}")

        # Prepare an embed to display all the user's input
        embed = discord.Embed(
            title="表單提交成功！",
            description="以下是您剛剛提交的資訊：",
            color=0x1ABC9C,
        )
        fields = [
            ("名字", user_data.get("name")),
            ("暱稱", user_data.get("nickname")),
            ("電子郵件", user_data.get("email")),
            ("電話號碼", user_data.get("phone")),
            ("高中階段", user_data.get("high_school_stage")),
            ("城市", user_data.get("city")),
            ("學校", user_data.get("school")),
        ]

        emergency_contact_info = (
            f"{emergency_contact_data['name']} ({emergency_contact_data['relationship']}) "
            f"- {emergency_contact_data['phone_number']}"
        )
        fields.append(("緊急聯絡人", emergency_contact_info))

        # Optional fields
        optional_fields = [
            ("Line ID", user_data.get("line_id")),
            ("Instagram ID", user_data.get("ig_id")),
            ("自我介紹", user_data.get("introduction")),
            ("組別", user_data.get("current_group")),
            ("身份", user_data.get("current_position")),
            ("主要職責", user_data.get("primary_role")),
            (
                "專長",
                ", ".join(user_data.get("expertise", []))
                if user_data.get("expertise")
                else None,
            ),
        ]

        for name, value in fields + optional_fields:
            if value:
                value = truncate(str(value))
                embed.add_field(name=name, value=value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


class ExistingMemberContactInfoModal(Modal):
    """Modal to collect contact information from existing members."""

    def __init__(self, user_id):
        super().__init__(title="聯絡資訊（選填）")
        self.user_id = user_id
        self.add_item(
            TextInput(
                label="Line ID",
                custom_id="line_id",
                required=False,
                placeholder="用於聯絡或通知",
            )
        )
        self.add_item(
            TextInput(
                label="Instagram ID",
                custom_id="ig_id",
                required=False,
            )
        )
        self.add_item(
            TextInput(
                label="自我介紹",
                custom_id="introduction",
                style=discord.TextStyle.long,
                required=False,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        user_data = get_user_data(self.user_id)
        user_data["line_id"] = self.children[0].value
        user_data["ig_id"] = self.children[1].value
        user_data["introduction"] = self.children[2].value
        set_user_data(self.user_id, user_data)

        embed = discord.Embed(
            title="聯絡資訊已完成！",
            description="太好了！請選擇您的組別以繼續。",
            color=0x3498DB,
        )

        from .views import ExistingMemberJobInfoSelectView

        view = ExistingMemberJobInfoSelectView(self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ExistingMemberInfoCollectionModal2(Modal):
    """Modal to collect additional basic information from existing members."""

    def __init__(self, user_id):
        super().__init__(title="收集基本資訊（2/2）")
        self.user_id = user_id
        self.add_item(
            TextInput(
                label="城市",
                custom_id="city",
                required=True,
                placeholder="如新竹市、新竹縣、臺中市",
            )
        )
        self.add_item(
            TextInput(
                label="學校",
                custom_id="school",
                required=True,
                placeholder="請填寫您的學校",
            )
        )
        self.add_item(
            TextInput(
                label="緊急聯絡人姓名",
                custom_id="emergency_contact_name",
                required=True,
            )
        )
        self.add_item(
            TextInput(
                label="緊急聯絡人關係",
                custom_id="emergency_contact_relationship",
                required=True,
            )
        )
        self.add_item(
            TextInput(
                label="緊急聯絡人電話",
                custom_id="emergency_contact_phone",
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        user_data = get_user_data(self.user_id)
        user_data["city"] = self.children[0].value
        user_data["school"] = self.children[1].value
        user_data["emergency_contact"] = {
            "name": self.children[2].value,
            "relationship": self.children[3].value,
            "phone_number": self.children[4].value,
        }
        set_user_data(self.user_id, user_data)

        embed = discord.Embed(
            title="第二部分已完成！",
            description="很棒！請點擊下方按鈕繼續填寫聯絡資訊。",
            color=0xE67E22,
        )

        from .views import ProceedToContactInfoView

        view = ProceedToContactInfoView(self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ExistingMemberInfoCollectionModal1(Modal):
    """Modal to collect basic information from existing members."""

    def __init__(self, user_id):
        super().__init__(title="收集基本資訊（1/2）")
        self.user_id = user_id
        self.add_item(
            TextInput(
                label="姓名",
                custom_id="name",
                required=True,
                placeholder="請填寫您的真實姓名",
            )
        )
        self.add_item(
            TextInput(
                label="暱稱",
                custom_id="nickname",
                required=True,
                placeholder="該如何稱呼你",
            )
        )
        self.add_item(
            TextInput(
                label="電子郵件",
                custom_id="email",
                required=True,
                placeholder="請填寫正確的電子郵件",
            )
        )
        self.add_item(
            TextInput(
                label="電話號碼",
                custom_id="phone",
                required=True,
                placeholder="請填寫正確的電話號碼",
            )
        )
        self.add_item(
            TextInput(
                label="高中階段",
                custom_id="high_school_stage",
                required=True,
                placeholder="高一、高二、高三、其他",
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("你無權使用此表單。", ephemeral=True)
            return

        if has_submitted_form(self.user_id):
            await interaction.response.send_message(
                "你已經填寫過表單，不能再次填寫。", ephemeral=True
            )
            return

        user_data = get_user_data(self.user_id)
        user_data["name"] = self.children[0].value
        user_data["nickname"] = self.children[1].value
        user_data["email"] = self.children[2].value
        user_data["phone"] = self.children[3].value
        user_data["high_school_stage"] = self.children[4].value
        set_user_data(self.user_id, user_data)

        embed = discord.Embed(
            title="第一部分已完成！",
            description="太棒了！請點擊下方按鈕繼續填寫下一部分。",
            color=0x9B59B6,
        )

        from .views import ProceedToInfoPart2View

        view = ProceedToInfoPart2View(self.user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
