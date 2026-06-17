from pathlib import Path

import pytest
from pytest_mock import MockerFixture
import pytest_asyncio
from cronboard.app import CronBoard
from cronboard.screens.CronCreator import CronCreator
from cronboard.screens.CronCreator import CronAutoComplete
from types import SimpleNamespace
from cronboard.screens.CronSSHModal import CronSSHModal
from collections.abc import AsyncIterator
from textual.pilot import Pilot
from cronboard.services.logging import cron_wrapper as mod


@pytest.fixture
def modal():
    yield CronSSHModal()


@pytest.fixture
def app(mocker: MockerFixture):
    fake_job = mocker.MagicMock()
    fake_job.comment = "test-job"
    fake_job.command = "echo hello"
    fake_job.render.return_value = "* * * * * echo hello"

    fake_cron = mocker.MagicMock()
    fake_cron.__iter__ = mocker.MagicMock(side_effect=lambda: iter([fake_job]))
    mocker.patch("cronboard.widgets.CronTable.CronTab", return_value=fake_cron)
    mocker.patch(
        "cronboard.screens.CronDeleteConfirmation.CronTab", return_value=fake_cron
    )
    yield CronBoard()


@pytest.fixture
def autocomplete():
    yield CronAutoComplete.__new__(CronAutoComplete)


@pytest_asyncio.fixture
async def pilot(app: CronBoard) -> AsyncIterator[Pilot]:
    async with app.run_test() as pilot_impl:
        yield pilot_impl


def make_creator(mocker: MockerFixture, **kwargs):
    cron = mocker.MagicMock()
    cron.__iter__ = mocker.MagicMock(return_value=iter([]))
    return CronCreator(cron, **kwargs)


def create_event(button_id: SimpleNamespace):
    event = SimpleNamespace()
    event.button = SimpleNamespace()
    event.button.id = button_id
    return event


def create_job_and_cron(mocker: MockerFixture):
    job = mocker.MagicMock()
    cron = mocker.MagicMock()
    return job, cron


def make_remote_command(mocker: MockerFixture, stderr_output=b"", exit_status=0):

    stdin = mocker.MagicMock()
    stdin.channel.recv_exit_status.return_value = exit_status

    stderr = mocker.MagicMock()
    stderr.read.return_value = stderr_output

    ssh_client = mocker.MagicMock()
    ssh_client.exec_command.return_value = (stdin, mocker.MagicMock(), stderr)
    return stdin, stderr, ssh_client


def make_query_one(mapping):
    def query_one(selector, *_args, **_kwargs):
        return mapping[selector]

    return query_one


def create_content(mocker: MockerFixture):
    return mocker.MagicMock()


def mock_ssh_exec_streams(
    mocker: MockerFixture,
    *,
    stdout: bytes = b"",
    stderr: bytes = b"",
):
    """Return stdout and stderr mocks whose read() returns the given bytes."""
    stdout_mock = mocker.Mock()
    stdout_mock.read.return_value = stdout
    stderr_mock = mocker.Mock()
    stderr_mock.read.return_value = stderr
    return stdout_mock, stderr_mock


def ssh_mock_exec_return(
    mocker: MockerFixture,
    *,
    stdout: bytes = b"",
    stderr: bytes = b"",
    stdin=None,
    spec: list[str] | None = None,
):
    """SSH mock whose every exec_command returns the same (stdin, stdout, stderr) streams."""
    ssh_mock = mocker.Mock(spec=spec) if spec is not None else mocker.Mock()
    stdout_mock, stderr_mock = mock_ssh_exec_streams(
        mocker, stdout=stdout, stderr=stderr
    )
    ssh_mock.exec_command.return_value = (stdin, stdout_mock, stderr_mock)
    return ssh_mock


def ssh_mock_exec_sequence(
    mocker: MockerFixture,
    responses: list[tuple[bytes, bytes]],
):
    """SSH mock: each exec_command consumes the next (stdout, stderr) payload in order."""
    ssh = mocker.Mock()
    tuples = []
    for stdout_b, stderr_b in responses:
        out_m, err_m = mock_ssh_exec_streams(mocker, stdout=stdout_b, stderr=stderr_b)
        tuples.append((None, out_m, err_m))
    ssh.exec_command.side_effect = tuples
    return ssh


def ssh_mock_exec_raises(mocker: MockerFixture, exc: BaseException):
    ssh_mock = mocker.Mock()
    ssh_mock.exec_command.side_effect = exc
    return ssh_mock


def ssh_mock_home_then_other(
    mocker: MockerFixture,
    *,
    home_stdout: bytes,
    other_stdout: bytes,
    home_stderr: bytes = b"",
    other_stderr: bytes = b"",
):
    """exec_command dispatches on cmd == \"echo $HOME\" vs subsequent commands."""
    ssh = mocker.Mock()

    def exec_command(cmd):
        mock_stdout = mocker.Mock()
        mock_stderr = mocker.Mock()
        if cmd == "echo $HOME":
            mock_stdout.read.return_value = home_stdout
            mock_stderr.read.return_value = home_stderr
        else:
            mock_stdout.read.return_value = other_stdout
            mock_stderr.read.return_value = other_stderr
        return (None, mock_stdout, mock_stderr)

    ssh.exec_command.side_effect = exec_command
    return ssh


def ssh_mock_install_remote_put_fail_exec(mocker: MockerFixture):
    """exec_command chain for install_wrapper_remote when SFTP put fails partway."""
    ssh = mocker.Mock()

    def exec_command(cmd):
        stdout, stderr = mock_ssh_exec_streams(mocker, stderr=b"")
        if cmd == "echo $HOME":
            stdout.read.return_value = b"/remote/home/user\n"
        elif "test -f" in cmd:
            stdout.read.return_value = b"MISSING\n"
        else:
            stdout.read.return_value = b""
        return (None, stdout, stderr)

    ssh.exec_command.side_effect = exec_command
    return ssh


def home_dir_under_tmp(tmp_path: Path, *, mkdir: bool = True) -> Path:
    home = tmp_path / "home"
    if mkdir:
        home.mkdir(parents=True)
    return home


def patch_config_dir(mocker: MockerFixture, home: Path) -> None:
    config_dir = home / ".config/cronboard"
    config_dir.mkdir(parents=True)
    mocker.patch.object(mod, "CONFIG_DIR", config_dir)


@pytest.fixture
def mock_bash(mocker: MockerFixture):

    return mocker.patch.object(mod.shutil, "which", return_value="/bin/bash")


@pytest.fixture
def mock_wrapper_installed(mocker: MockerFixture):

    return mocker.patch.object(
        mod, "install_wrapper", return_value="/tmp/cron-wrapper.sh"
    )
