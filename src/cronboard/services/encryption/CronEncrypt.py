from cryptography.fernet import Fernet
import os
from cronboard.config import CONFIG_DIR, KEY_FILE


def get_or_create_key():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        os.chmod(KEY_FILE, 0o600)
    else:
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    return key


fernet = Fernet(get_or_create_key())


def encrypt_password(password: str) -> str:
    if not password:
        return ""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    if not token:
        return ""

    return fernet.decrypt(token.encode()).decode()
