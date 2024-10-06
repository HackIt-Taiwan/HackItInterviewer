# app/models/encrypted_string_field.py
from mongoengine import StringField
from app.utils.encryption import aes_encrypt, aes_decrypt


class EncryptedStringField(StringField):
    """Custom field for encrypted strings."""
    prefix = "ENC::"  # Prefix to identify encrypted strings

    def to_mongo(self, value):
        if value is not None:
            if not value.startswith(self.prefix):
                encrypted_value = aes_encrypt(value)
                return f"{self.prefix}{encrypted_value}"
            return value
        return super().to_mongo(value)

    def to_python(self, value):
        if value is not None:
            try:
                # Check if the value is encrypted
                if value.startswith(self.prefix):
                    encrypted_value = value[len(self.prefix):]
                    return aes_decrypt(encrypted_value)
                return value
            except Exception as e:
                print(f"Decryption error: {e}")
        return super().to_python(value)
