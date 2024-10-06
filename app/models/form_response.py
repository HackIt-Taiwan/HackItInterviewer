# app/models/form_response.py
import uuid
from mongoengine import Document, ListField, EmbeddedDocumentField, UUIDField
from app.models.encrypted_string_field import EncryptedStringField


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

    meta = {'collection': 'form_response'}
