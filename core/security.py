import base64
import os
from cryptography.fernet import Fernet
from django.conf import settings

def get_encryptor():
    """Encryption keyni .env dan o'qiydi yoki settings dan oladi"""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        # Agar key bo'lmasa, proyektni to'xtatmaslik uchun vaqtinchalik key (lekin bu xavfli)
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode())
    return Fernet(key)

def encrypt_data(data: str) -> str:
    if not data: return ""
    f = get_encryptor()
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data: return ""
    try:
        f = get_encryptor()
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return "[Shifrlangan ma'lumot]"
