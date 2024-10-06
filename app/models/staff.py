# app/models/staff.py
import uuid
from datetime import datetime

from mongoengine import Document, UUIDField, StringField, IntField, ListField, DateTimeField, EmbeddedDocumentField, \
    BooleanField
from app.models.encrypted_string_field import EncryptedStringField

class ProjectHistory(Document):
    """Model representing project history."""

    # Basic information
    project_name = EncryptedStringField(required=True)
    project_role = EncryptedStringField(required=True)
    project_start_date = DateTimeField(required=True)
    project_end_date = DateTimeField(required=True)


class EmergencyContact(Document):
    """Model representing emergency contacts."""

    # Basic personal information
    name = EncryptedStringField(required=True)
    relationship = EncryptedStringField(required=True)
    phone_number = EncryptedStringField(required=True)


class Staff(Document):
    """Model representing staff members."""

    # Unique identifier
    uuid = UUIDField(default=uuid.uuid4, primary_key=True)

    # Basic personal information
    name = EncryptedStringField(required=True)
    nickname = EncryptedStringField(required=False)
    email = EncryptedStringField(required=True)
    phone_number = EncryptedStringField(required=True)
    high_school_stage = EncryptedStringField(required=True)
    city = EncryptedStringField(required=True)
    school = EncryptedStringField(required=False)
    emergency_contact = EmbeddedDocumentField('EmergencyContact', required=False)

    # Contact info
    line_id = EncryptedStringField(required=False)
    ig_id = EncryptedStringField(required=False)
    discord_id = EncryptedStringField(required=False)

    # Work-related information
    current_group = EncryptedStringField(required=True)             # 組別
    current_position = EncryptedStringField(required=True)          # 身份
    primary_role = EncryptedStringField(required=False)              # 主要職責
    expertise = ListField(EncryptedStringField(), required=False)   # 專長
    employment_status = EncryptedStringField(required=False, choices=['busy', 'normal', 'idle'])       # 空閒狀態
    active_status = EncryptedStringField(required=False, choices=['Active', 'Inactive', 'Suspended'])  # 活躍狀態

    # Permission level (-1, 0, 1, 2, 3, 4, 5, 6)
    permission_level = IntField(default=0, choices=[-1, 0, 1, 2, 3, 4, 5, 6])

    # Additional details
    introduction = EncryptedStringField(required=False)
    avatar_base64 = StringField(required=False)
    join_date = DateTimeField(default=datetime.utcnow)
    leave_date = DateTimeField(required=False)
    project_history = EmbeddedDocumentField('ProjectHistory', required=False)

    # For identifying staff members or for system integration
    discord_user_id = EncryptedStringField(required=False)
    role_history = ListField(EncryptedStringField(), required=False)
    attendance_records = ListField(EncryptedStringField(), required=False)
    last_login = EncryptedStringField(required=False)
    is_signup = BooleanField(default=False)

    # TODO system integration
    available_time_slots = ListField(EncryptedStringField(), required=False)  # 未來將與日曆整合

    # Meta information
    meta = {'collection': 'staff'}

