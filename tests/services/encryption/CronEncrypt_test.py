from cronboard.services.encryption.CronEncrypt import encrypt_password, decrypt_password
import pytest


@pytest.mark.parametrize("password", [""])
def test_encrypt_empty_password(password):
    encrypted = encrypt_password(password)
    assert encrypted == ""


@pytest.mark.parametrize("password", [""])
def test_decrypt_empty_password(password):
    decrypted = decrypt_password(password)
    assert decrypted == ""


@pytest.mark.parametrize("password", ["mysecretpassword"])
def test_encrupt_decrypt_roundtrip(password):
    encrypted = encrypt_password(password)
    decrypted = decrypt_password(encrypted)
    assert decrypted == password
