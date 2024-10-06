# app/models/form_response.py
import uuid
from mongoengine import Document, ListField, UUIDField, StringField, BooleanField, EnumField
from app.models.encrypted_string_field import EncryptedStringField
from enum import Enum


class InterviewStatus(Enum):
    NOT_ACCEPTED = "未受理"
    NOT_CONTACTED = "尚未聯繫"
    EMAIL_SENT = "已發送郵件（試圖安排面試）"
    INTERVIEW_SCHEDULED = "面試已安排"
    NO_SHOW = "未出席面試"
    TRANSFERRED_TO_ANOTHER_TEAM = "轉接至他組"
    INTERVIEW_PASSED_WAITING_MANAGER_FORM = "面試通過（等待負責人填寫表單）"
    INTERVIEW_PASSED_WAITING_FOR_FORM = "面試通過（等待註冊）"
    INTERVIEW_PASSED = "面試通過"
    INTERVIEW_FAILED = "面試失敗"
    CANCELLED = "已取消"


class FormResponse(Document):
    """For storing responses from the form."""
    uuid = UUIDField(default=uuid.uuid4, primary_key=True)
    name = EncryptedStringField(required=True)
    email = EncryptedStringField(required=True)
    phone_number = EncryptedStringField(required=True)
    high_school_stage = EncryptedStringField(required=True)
    city = EncryptedStringField(required=True)
    interested_fields = ListField(EncryptedStringField(), required=True)
    preferred_order = EncryptedStringField(required=False)
    reason_for_choice = EncryptedStringField(required=True)
    related_experience = EncryptedStringField(required=True)
    signature_url = EncryptedStringField(required=True)

    email_hash = StringField(required=True)
    is_duplicate = BooleanField(default=False)

    # Interview process fields
    interview_status = EnumField(InterviewStatus, default=InterviewStatus.NOT_ACCEPTED)  # 面試狀態
    is_email_contacted = BooleanField(default=False)            # 問題 1: 是否已透過 Email 聯絡對方
    is_interview_scheduled = BooleanField(default=False)        # 問題 2: 是否已與對方約好會議時間
    is_attended_interview = BooleanField(default=False)         # 問題 3: 是否出席原安排的會議
    is_interview_passed = BooleanField(default=False)           # 問題 4: 面試通過？
    is_form_completed_by_manager = BooleanField(default=False)  # 問題 5: 由負責人填寫表單
    is_registered = BooleanField(default=False)                 # 問題 6: 是否已註冊

    manager_id = EncryptedStringField(required=False) # 負責人 ID
    history = ListField(EncryptedStringField(), required=False)  # 歷史紀錄


    meta = {'collection': 'form_response'}
