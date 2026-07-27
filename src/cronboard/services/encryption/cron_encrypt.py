import os
import subprocess

from cryptography.fernet import Fernet

from cronboard.config import CONFIG_DIR, KEY_FILE


def get_or_create_key() -> bytes:
    """Creates a new key if it doesn't exist, or returns the existing key.

    Returns:
        The key as a bytes object.
    """

    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(KEY_FILE):
        key: bytes = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        os.chmod(KEY_FILE, 0o600)
    else:
        with open(KEY_FILE, "rb") as key_file:
            key: bytes = key_file.read()
    return key


fernet: Fernet = Fernet(get_or_create_key())


def encrypt_password(password: str) -> str:
    """Encrypts the password using Fernet.

    Args:
        password: The password to encrypt.

    Returns:
        The encrypted password as a string.
    """

    if not password:
        return ""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    """Decrypts the password using Fernet.

    Args:
        token: The encrypted password as a string.

    Returns:
        The decrypted password as a string.
    """

    if not token:
        return ""

    return fernet.decrypt(token.encode()).decode()


def encrypt_telegram_token(token: str) -> str:
    """Encrypts the Telegram token using OpenSSL.

    Args:
        token: The Telegram token to encrypt.

    Returns:
        The encrypted Telegram token as a string.
    """

    if not token:
        return ""
    return subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-salt",
            "-pbkdf2",
            "-pass",
            "file:" + str(KEY_FILE),
            "-base64",
            "-A",
        ],
        input=token.encode(),
        capture_output=True,
        check=False,
    ).stdout.decode()


def decrypt_telegram_token(token: str) -> str:
    """Decrypts the Telegram token using OpenSSL.

    Args:
        token: The encrypted Telegram token as a string.

    Returns:
        The decrypted Telegram token as a string.
    """

    if not token:
        return ""
    return subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-salt",
            "-pbkdf2",
            "-pass",
            "file:" + str(KEY_FILE),
            "-base64",
            "-A",
        ],
        input=token.encode(),
        capture_output=True,
        check=False,
    ).stdout.decode()
