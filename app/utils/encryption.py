# app/utils/encryption.py
import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

AES_BLOCK_SIZE = 16  # AES block size for CBC mode

def _get_encryption_key():
    """Retrieve the AES-256 encryption key from the environment variables."""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY is not set in the environment variables.")
    if len(key.encode()) < 32:
        raise ValueError("Encryption key must be at least 32 bytes (256 bits) for AES-256.")
    return key.encode()[:32]

def aes_encrypt(data):
    """AES encrypt the data using a randomly generated IV each time for security."""
    key = _get_encryption_key()
    iv = get_random_bytes(AES_BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES_BLOCK_SIZE))
    iv_encoded = base64.urlsafe_b64encode(cipher.iv).decode('utf-8').rstrip('=')
    ct_encoded = base64.urlsafe_b64encode(ct_bytes).decode('utf-8').rstrip('=')
    return f"{iv_encoded}:{ct_encoded}"

def aes_decrypt(encrypted_data):
    """AES decrypt the data using the provided key and IV."""
    key = _get_encryption_key()
    try:
        iv, ct = encrypted_data.split(':')
        iv = base64.urlsafe_b64decode(iv + '==')
        ct = base64.urlsafe_b64decode(ct + '==')
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES_BLOCK_SIZE)
        return pt.decode('utf-8')
    except (ValueError, KeyError) as e:
        raise ValueError(f"Decryption failed: {e}")
