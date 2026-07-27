import base64
import binascii
import os
import shlex
import shutil
import stat
from pathlib import Path
from typing import Optional

import paramiko
import tomlkit
from paramiko.sftp_client import SFTPClient

from cronboard.config import (
    CONFIG_DIR,
    CONFIG_REL_PATH,
    CRONBOARD_CONFIG_FILE,
    KEY_FILE,
    WRAPPER_DIST,
    WRAPPER_SOURCE,
)
from cronboard.services.cron_dir_entry import CronDirEntry

"""
Prefix for base64-encoded user command in wrapped crontab lines (avoids shell
metacharacters and nested-quote breakage). Legacy wrapped lines without this
prefix still run via the wrapper's multi-argument branch.
"""

COMMAND_PAYLOAD_PREFIX = "cronboard1:"


def get_remote_bash_path(ssh: paramiko.SSHClient) -> str:
    """Gets the path to the bash executable on the remote server.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        The path to the bash executable on the remote server if found, else "/bin/bash".
    """

    try:
        _, stdout, _ = ssh.exec_command("command -v bash")
        result: str = stdout.read().decode().strip()
        if result:
            return result
    except Exception:
        pass
    return "/bin/bash"


def get_remote_home(ssh: paramiko.SSHClient) -> Optional[str]:
    """Gets the home directory on the remote server.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        The home directory on the remote server if found, else None.
    """

    try:
        _, stdout, stderr = ssh.exec_command("echo ~")
        home: str = stdout.read().decode().strip()
        err: str = stderr.read().decode().strip()

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


def get_files(
    ssh: paramiko.SSHClient, path: str, sftp: SFTPClient | None = None
) -> list[CronDirEntry]:
    """Gets the files and directories in the given path.

    Args:
        ssh: Paramiko SSH client for remote operations.
        path: The current path.
        sftp: SFTP client for local operations on the server.

    Returns:
        A list of CronDirEntry objects with the files and directories in the given path.
    """

    own_sftp: bool = sftp is None

    if own_sftp:
        sftp: SFTPClient = ssh.open_sftp()

    entries: list[CronDirEntry] = []

    try:
        for object in sftp.listdir_attr(path):
            if stat.S_ISDIR(object.st_mode):
                cron_dir_entry = CronDirEntry(object.filename, path, True)
                entries.append(cron_dir_entry)
            else:
                cron_file_entry = CronDirEntry(object.filename, path, False)
                entries.append(cron_file_entry)
        return entries
    finally:
        if own_sftp:
            sftp.close()


def is_wrapper_installed_local() -> bool:
    """Checks if the log wrapper is installed locally.

    Returns:
        True if the log wrapper is installed locally, else False.
    """

    target_file: Path = CONFIG_DIR / WRAPPER_DIST

    return (
        target_file.exists()
        and target_file.is_file()
        and os.access(target_file, os.X_OK)
    )


def is_wrapper_installed_remote(ssh: paramiko.SSHClient) -> bool:
    """Checks if the log wrapper is installed on the remote server.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        True if the log wrapper is installed on the remote server, else False.
    """

    home: str | None = get_remote_home(ssh)
    if not home:
        return False

    remote_file = f"{home}/{CONFIG_REL_PATH}/{WRAPPER_DIST}"

    _, stdout, stderr = ssh.exec_command(
        f"test -f {remote_file} && test -x {remote_file} && echo OK || echo MISSING"
    )

    result: str = stdout.read().decode().strip()
    err: str = stderr.read().decode().strip()

    if err:
        print(f"Error: {err}")
        return False

    return result == "OK"


def is_wrapper_installed(ssh: paramiko.SSHClient | None = None) -> bool:
    """Checks if the log wrapper is installed on the remote server or locally.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        True if the log wrapper is installed on the remote server or locally, else False.
    """

    if ssh is None:
        return is_wrapper_installed_local()
    else:
        return is_wrapper_installed_remote(ssh)


def install_wrapper_local():
    """Installs the log wrapper locally.

    Returns:
        The path to the log wrapper if installed, else None.
    """

    target_dir: Path = CONFIG_DIR
    target_file: Path = CONFIG_DIR / WRAPPER_DIST

    target_dir.mkdir(parents=True, exist_ok=True)

    with open(WRAPPER_SOURCE, "rb") as src, open(target_file, "wb") as dst:
        dst.write(src.read())

    target_file.chmod(target_file.stat().st_mode | stat.S_IEXEC)

    return str(target_file)


def install_wrapper_remote(ssh: paramiko.SSHClient) -> str | None:
    """Installs the log wrapper on the remote server.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        The path to the log wrapper on the remote server if installed, else None.
    """

    home: str | None = get_remote_home(ssh)

    remote_dir = f"{home}/{CONFIG_REL_PATH}"
    remote_file = f"{remote_dir}/{WRAPPER_DIST}"
    remote_key = f"{remote_dir}/secret.key"
    remote_config = f"{remote_dir}/config.toml"

    sftp: SFTPClient = ssh.open_sftp()

    try:
        ssh.exec_command(f"mkdir -p {remote_dir}")
        sftp.put(str(WRAPPER_SOURCE), remote_file)
        ssh.exec_command(f"chmod +x {remote_file}")

        sftp.put(str(KEY_FILE), remote_key)
        ssh.exec_command(f"chmod 600 {remote_key}")

        config_content = _generate_telegram_config()
        with sftp.open(remote_config, "w") as f:
            f.write(config_content)

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        sftp.close()

    return remote_file


def _generate_telegram_config() -> str:
    """Generates a minimal config.toml with only Telegram settings."""

    try:
        with open(CRONBOARD_CONFIG_FILE, "r") as f:
            config: dict = tomlkit.loads(f.read())
        minimal: dict = tomlkit.document()
        minimal["telegram_token"] = config.get("telegram_token", "")
        minimal["telegram_chat_id"] = config.get("telegram_chat_id", "")
        return tomlkit.dumps(minimal)
    except Exception as e:
        print(f"Error: {e}")
        return ""


def install_wrapper(ssh: paramiko.SSHClient | None = None) -> str | None:
    """Installs the log wrapper on the remote server or locally.

    Args:
        ssh: Paramiko SSH client for remote operations.

    Returns:
        The path to the log wrapper on the remote server or locally if installed, else None.
    """

    if ssh is None:
        return install_wrapper_local()
    else:
        return install_wrapper_remote(ssh)


def _encode_wrapped_command_payload(command: str) -> str:
    b64: str = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return f"{COMMAND_PAYLOAD_PREFIX}{b64}"


def _decode_wrapped_command_payload(token: str) -> str | None:
    if not token.startswith(COMMAND_PAYLOAD_PREFIX):
        return None
    raw_b64: str = token[len(COMMAND_PAYLOAD_PREFIX) :]
    try:
        return base64.b64decode(raw_b64, validate=True).decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        return None


def wrap_command(
    command: str, identificator: str, ssh: paramiko.SSHClient | None = None
) -> str:
    """Wraps the cronjob's command with the log wrapper.

    Args:
        command: The command to wrap.
        identificator: The identificator of the cronjob.
        ssh: Paramiko SSH client for remote operations.

    Returns:
        The wrapped command if the wrapper is installed, else the original command.
    """

    wrapper_path: str | None = install_wrapper(ssh)
    if wrapper_path is None:
        # If this is None, it means failed to install wrapper in ssh server
        return command

    if ssh is not None:
        bash_path: str = get_remote_bash_path(ssh)
    else:
        bash_path: str = shutil.which("bash") or "/bin/bash"
    try:
        parts: list[str] = shlex.split(command)
    except ValueError:
        # If it can't be parsed, just wrap it (safer than guessing)
        parts: list[str] = []

    # Confirm if it already wrapped
    if (
        len(parts) >= 3
        and parts[0] == bash_path
        and parts[1].endswith("cron-wrapper.sh")
    ):
        return command
    payload: str = _encode_wrapped_command_payload(command)
    return (
        f"{shlex.quote(bash_path)} {shlex.quote(wrapper_path)} "
        f"{shlex.quote(identificator)} {shlex.quote(payload)}"
    )


def has_wrapper(command: str) -> bool:
    """Checks if the command has the log wrapper.

    Args:
        command: The command to check.

    Returns:
        True if the command has the log wrapper, else False.
    """

    try:
        parts: list[str] = shlex.split(command)
    except ValueError:
        return False

    if len(parts) < 4:
        return False

    if not parts[0].endswith("/bash"):
        return False

    wrapper_path: str = parts[1]

    return (
        wrapper_path.endswith("cron-wrapper.sh") and bool(parts[2])  # identificator
    )


def command_without_wrapper(command: str) -> str:
    """Removes the log wrapper from the command.

    Args:
        command: The command to remove the log wrapper from.

    Returns:
        The command without the log wrapper if it was found, else the original command.
    """

    try:
        parts: list[str] = shlex.split(command)
    except ValueError:
        return command

    if len(parts) < 4:
        return command

    if not parts[0].endswith("/bash"):
        return command

    wrapper_path: str = parts[1]

    if not wrapper_path.endswith("cron-wrapper.sh"):
        return command

    # strip: bash + wrapper + identificator
    if len(parts) < 4:
        return command
    decoded: str | None = _decode_wrapped_command_payload(parts[3])
    if decoded is not None:
        return decoded
    # Legacy: remainder was split as argv words; best-effort rejoin.
    return " ".join(parts[3:])
