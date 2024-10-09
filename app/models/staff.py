# app/models/staff.py
import uuid
from datetime import datetime

from mongoengine import Document, UUIDField, StringField, IntField, ListField, DateTimeField, EmbeddedDocumentField, \
    BooleanField, EmbeddedDocument
from app.models.encrypted_string_field import EncryptedStringField

class ProjectHistory(EmbeddedDocument):
    """Model representing project history."""

    # Basic information
    project_name = EncryptedStringField(required=True)
    project_role = EncryptedStringField(required=True)
    project_start_date = DateTimeField(required=True)
    project_end_date = DateTimeField(required=True)


class EmergencyContact(EmbeddedDocument):
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
    introduction = EncryptedStringField(required=False)

    # Work-related information
    current_group = StringField(required=True, choices=['HackIt', '策劃部', '設計部', '行政部', '公關組', '活動企劃組',
                                                        '美術組', '資訊組', '影音組', '行政組', '財務組', '其他'])
    current_position = EncryptedStringField(required=True)            # 身份
    primary_role = EncryptedStringField(required=False)               # 主要職責
    expertise = ListField(EncryptedStringField(), required=False)     # 專長
    # project_now = ListField(EncryptedStringField(), required=False)   # TODO: 現在參與的專案 EmbeddedDocumentField
    # task_now = ListField(EncryptedStringField(), required=False)      # TODO: 現在的任務 EmbeddedDocumentField
    employment_status = StringField(required=False, choices=['busy', 'normal', 'idle'])       # 空閒狀態
    active_status = StringField(required=False, choices=['Active', 'Inactive', 'Suspended'])  # 活躍狀態

    # Permission level (-1, 0, 1, 2, 3, 4, 5, 6)
    permission_level = IntField(default=2, choices=[-1, 0, 1, 2, 3, 4, 5, 6])
    # -1: 封殺；0: 成員；1: 組副負責人；2: 組負責人；3: 部負責人；4: 負責人；5: 顧問；6: 外星人

    # Additional details
    avatar_base64 = StringField(required=False)
    join_date = DateTimeField(default=datetime.utcnow)
    leave_date = DateTimeField(required=False)
    project_history = EmbeddedDocumentField('ProjectHistory', required=False)

    # For identifying staff members or for system integration
    discord_user_id = StringField(required=False)
    role_history = ListField(EncryptedStringField(), required=False)
    attendance_records = ListField(EncryptedStringField(), required=False)
    last_login = EncryptedStringField(required=False)
    is_signup = BooleanField(default=False)

    # TODO system integration
    available_time_slots = ListField(EncryptedStringField(), required=False)  # 未來將與日曆整合

    # Meta information
    meta = {'collection': 'staff'}

