import paramiko
import shlex
from pathlib import Path
import posixpath
from cronboard.services.logging.cron_wrapper import get_remote_home
from cronboard.config import LOG_DIR, LOG_REL_PATH
import shutil


def get_log_files(identificator: str, ssh: paramiko.SSHClient | None = None):
    if ssh is None:
        log_dir = LOG_DIR / identificator
        if not log_dir.exists():
            return {}
        return {
            p.stem: str(p)
            for p in sorted(
                log_dir.glob(f"{identificator}_*.log"), key=lambda p: p.stem
            )
        }
    else:
        home = get_remote_home(ssh)
        if not home:
            return {}
        log_dir = posixpath.join(home, LOG_REL_PATH, identificator)

        cmd = f"ls {log_dir} 2>/dev/null"
        _, stdout, stderr = ssh.exec_command(cmd)
        files = stdout.read().decode().splitlines()
        errors = stderr.read().decode().strip()

        if errors:
            print(f"Error: {errors}")
            return {}

        result = {}
        for file in sorted(files):
            if file.startswith(f"{identificator}_") and file.endswith(".log"):
                stem = file[:-4]  # remove ".log"
                full_path = posixpath.join(log_dir, file)
                result[stem] = full_path

        return result


def read_log_file(log_path: str, ssh: paramiko.SSHClient | None = None):
    if ssh is None:
        log_file = Path(log_path)
        if not log_file.exists():
            return []
        with open(log_file, "r") as f:
            return f.readlines()
    else:
        safe_path = shlex.quote(log_path)

        _, stdout, stderr = ssh.exec_command(f"test -f {safe_path} && cat {safe_path}")
        output = stdout.read().decode()
        error = stderr.read().decode()

        if not output or error:
            if error:
                print(f"Error: {error}")
            return []

        return output.splitlines(keepends=True)


def delete_logs_for_identificator(
    identificator: str, ssh: paramiko.SSHClient | None = None
) -> None:
    """
    Deletes all log files associated with the given identificator.
    """
    if ssh is None:
        path = LOG_DIR / identificator
        shutil.rmtree(path, ignore_errors=True)
    else:
        home = get_remote_home(ssh)

        if not home:
            return

        path = posixpath.join(home, LOG_REL_PATH, identificator)
        ssh.exec_command(f"rm -rf -- {shlex.quote(path)}")
