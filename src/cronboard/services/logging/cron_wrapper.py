import base64
import binascii
import os
import stat
import paramiko
import shlex
import shutil
from typing import Optional
from cronboard.config import WRAPPER_SOURCE, CONFIG_DIR, CONFIG_REL_PATH, WRAPPER_DIST

"""
Prefix for base64-encoded user command in wrapped crontab lines (avoids shell
metacharacters and nested-quote breakage). Legacy wrapped lines without this
prefix still run via the wrapper's multi-argument branch.
"""

COMMAND_PAYLOAD_PREFIX = "cronboard1:"


def get_remote_bash_path(ssh: paramiko.SSHClient) -> str:
    try:
        _, stdout, _ = ssh.exec_command("command -v bash")
        result = stdout.read().decode().strip()
        if result:
            return result
    except Exception:
        pass
    return "/bin/bash"


def get_remote_home(ssh: paramiko.SSHClient) -> Optional[str]:
    try:
        _, stdout, stderr = ssh.exec_command("echo ~")
        home = stdout.read().decode().strip()
        err = stderr.read().decode().strip()

        if err:
            print(f"Error: Failed to get HOME: {err}")
            return None

        if not home:
            print("Error: HOME directory is empty")
            return None

        return home

    except paramiko.SSHException as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def is_wrapper_installed_local() -> bool:
    target_file = CONFIG_DIR / WRAPPER_DIST

    return (
        target_file.exists()
        and target_file.is_file()
        and os.access(target_file, os.X_OK)
    )


def is_wrapper_installed_remote(ssh: paramiko.SSHClient) -> bool:
    home = get_remote_home(ssh)
    if not home:
        return False

    remote_file = f"{home}/{CONFIG_REL_PATH}/{WRAPPER_DIST}"

    _, stdout, stderr = ssh.exec_command(
        f"test -f {remote_file} && test -x {remote_file} && echo OK || echo MISSING"
    )

    result = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if err:
        print(f"Error: {err}")
        return False

    return result == "OK"


def is_wrapper_installed(ssh: paramiko.SSHClient | None = None) -> bool:
    if ssh is None:
        return is_wrapper_installed_local()
    else:
        return is_wrapper_installed_remote(ssh)


def install_wrapper_local():
    target_dir = CONFIG_DIR
    target_file = CONFIG_DIR / WRAPPER_DIST

    target_dir.mkdir(parents=True, exist_ok=True)

    with open(WRAPPER_SOURCE, "rb") as src, open(target_file, "wb") as dst:
        dst.write(src.read())

    target_file.chmod(target_file.stat().st_mode | stat.S_IEXEC)

    return str(target_file)


def install_wrapper_remote(ssh: paramiko.SSHClient):
    home = get_remote_home(ssh)

    remote_dir = f"{home}/{CONFIG_REL_PATH}"
    remote_file = f"{remote_dir}/{WRAPPER_DIST}"

    sftp = ssh.open_sftp()

    try:
        ssh.exec_command(f"mkdir -p {remote_dir}")
        sftp.put(str(WRAPPER_SOURCE), remote_file)
        ssh.exec_command(f"chmod +x {remote_file}")
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sftp.close()

    return remote_file


def install_wrapper(ssh: paramiko.SSHClient | None = None):
    if ssh is None:
        return install_wrapper_local()
    else:
        return install_wrapper_remote(ssh)


def _encode_wrapped_command_payload(command: str) -> str:
    b64 = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return f"{COMMAND_PAYLOAD_PREFIX}{b64}"


def _decode_wrapped_command_payload(token: str) -> str | None:
    if not token.startswith(COMMAND_PAYLOAD_PREFIX):
        return None
    raw_b64 = token[len(COMMAND_PAYLOAD_PREFIX) :]
    try:
        return base64.b64decode(raw_b64, validate=True).decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        return None


def wrap_command(
    command: str, identificator: str, ssh: paramiko.SSHClient | None = None
):
    wrapper_path = install_wrapper(ssh)
    if wrapper_path is None:
        # If this is None, it means failed to install wrapper in ssh server
        return command

    if ssh is not None:
        bash_path = get_remote_bash_path(ssh)
    else:
        bash_path = shutil.which("bash") or "/bin/bash"
    try:
        parts = shlex.split(command)
    except ValueError:
        # If it can't be parsed, just wrap it (safer than guessing)
        parts = []

    # Confirm if it already wrapped
    if (
        len(parts) >= 3
        and parts[0] == bash_path
        and parts[1].endswith("cron-wrapper.sh")
    ):
        return command
    payload = _encode_wrapped_command_payload(command)
    return (
        f"{shlex.quote(bash_path)} {shlex.quote(wrapper_path)} "
        f"{shlex.quote(identificator)} {shlex.quote(payload)}"
    )


def has_wrapper(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False

    if len(parts) < 4:
        return False

    if not parts[0].endswith("/bash"):
        return False

    wrapper_path = parts[1]

    return (
        wrapper_path.endswith("cron-wrapper.sh") and bool(parts[2])  # identificator
    )


def command_without_wrapper(command: str):
    try:
        parts = shlex.split(command)
    except ValueError:
        return command

    if len(parts) < 4:
        return command

    if not parts[0].endswith("/bash"):
        return command

    wrapper_path = parts[1]

    if not wrapper_path.endswith("cron-wrapper.sh"):
        return command

    # strip: bash + wrapper + identificator
    if len(parts) < 4:
        return command
    decoded = _decode_wrapped_command_payload(parts[3])
    if decoded is not None:
        return decoded
    # Legacy: remainder was split as argv words; best-effort rejoin.
    return " ".join(parts[3:])
