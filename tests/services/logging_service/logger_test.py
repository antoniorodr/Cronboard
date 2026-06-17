from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cronboard.services.logging.logger import (
    delete_logs_for_identificator,
    get_log_files,
    read_log_file,
)

from tests.conftest import ssh_mock_exec_return, ssh_mock_exec_sequence

_LOGGER = "cronboard.services.logging.logger"
_FAKE_HOME = Path("/fake/home")


def _patch_local_log_discovery(
    mocker: MockerFixture,
    *,
    dir_exists: bool,
    glob_paths: list[Path] | None = None,
) -> None:
    mock_log_dir = mocker.Mock()
    mock_log_dir.exists.return_value = dir_exists
    mock_log_dir.glob.return_value = glob_paths or []
    mock_log_dir.__truediv__ = mocker.Mock(return_value=mock_log_dir)
    mocker.patch(f"{_LOGGER}.LOG_DIR", mock_log_dir)


def _patch_logger_path_and_instance(
    mocker: MockerFixture,
    *,
    exists: bool,
) -> None:
    mock_cls = mocker.patch(f"{_LOGGER}.Path")
    fake_path = mocker.Mock()
    fake_path.exists.return_value = exists
    mock_cls.return_value = fake_path


def test_get_log_files_returns_empty_when_dir_missing(mocker: MockerFixture):
    _patch_local_log_discovery(mocker, dir_exists=False)

    assert get_log_files("app1", ssh=None) == {}


def test_get_log_files_returns_dict(mocker: MockerFixture):
    fake_file1 = _FAKE_HOME / ".config/cronboard/logs/app1_log1.log"
    fake_file2 = _FAKE_HOME / ".config/cronboard/logs/app1_log2.log"

    _patch_local_log_discovery(
        mocker,
        dir_exists=True,
        glob_paths=[fake_file1, fake_file2],
    )

    assert get_log_files("app1", ssh=None) == {
        "app1_log1": str(fake_file1),
        "app1_log2": str(fake_file2),
    }


def test_get_log_files_returns_empty_dict_when_no_log_files_match_glob(
    mocker: MockerFixture,
):
    _patch_local_log_discovery(mocker, dir_exists=True, glob_paths=[])

    assert get_log_files("app1", ssh=None) == {}


def test_get_log_files_ssh_returns_empty_when_remote_home_unavailable(
    mocker: MockerFixture,
):
    mocker.patch(f"{_LOGGER}.get_remote_home", return_value=None)
    ssh = mocker.Mock()

    assert get_log_files("app1", ssh=ssh) == {}


@pytest.mark.parametrize(
    ("ls_read", "expected"),
    [
        (
            b"""app1_a.log
app1_b.log
app2_c.log
random.txt
""",
            {
                "app1_a": "/home/test/.config/cronboard/logs/app1/app1_a.log",
                "app1_b": "/home/test/.config/cronboard/logs/app1/app1_b.log",
            },
        ),
        (
            b"""other.log
file.txt
""",
            {},
        ),
    ],
    ids=["filtered", "no_match"],
)
def test_get_log_files_ssh(mocker: MockerFixture, ls_read: bytes, expected: dict):
    ssh = ssh_mock_exec_sequence(
        mocker,
        [(b"/home/test\n", b""), (ls_read, b"")],
    )

    assert get_log_files("app1", ssh=ssh) == expected


def test_read_log_file_returns_no_logs_when_missing(mocker: MockerFixture):
    _patch_logger_path_and_instance(mocker, exists=False)

    assert read_log_file("/fake/path.log", ssh=None) == []


def test_read_log_file_returns_lines(mocker: MockerFixture):
    _patch_logger_path_and_instance(mocker, exists=True)

    mock_open = mocker.mock_open(read_data="line1\nline2\nline3\n")
    mocker.patch("builtins.open", mock_open)

    assert read_log_file("/fake/path.log", ssh=None) == [
        "line1\n",
        "line2\n",
        "line3\n",
    ]


@pytest.mark.parametrize(
    ("stdout_read", "stderr_read", "remote_path", "expected"),
    [
        (
            b"line1\nline2\n",
            b"",
            "/remote/log.log",
            ["line1\n", "line2\n"],
        ),
        (
            b"",
            b"some error",
            "/remote/missing.log",
            [],
        ),
    ],
    ids=["success", "missing"],
)
def test_read_log_file_ssh(
    mocker: MockerFixture,
    stdout_read: bytes,
    stderr_read: bytes,
    remote_path: str,
    expected: list[str],
):
    ssh = ssh_mock_exec_return(
        mocker,
        stdout=stdout_read,
        stderr=stderr_read,
    )

    assert read_log_file(remote_path, ssh=ssh) == expected


def test_read_log_file_ssh_empty_stdout_and_stderr(mocker: MockerFixture):
    ssh = ssh_mock_exec_return(mocker, stdout=b"", stderr=b"")

    assert read_log_file("/remote/empty.log", ssh=ssh) == []


def test_read_log_file_ssh_returns_empty_when_stderr_has_noise(
    mocker: MockerFixture,
):
    ssh = ssh_mock_exec_return(
        mocker,
        stdout=b"line\n",
        stderr=b"warning: cat wrote to stderr\n",
    )

    assert read_log_file("/remote/log.log", ssh=ssh) == []


def test_delete_logs_for_identificator_local_removes_matching_files(
    mocker: MockerFixture, tmp_path: Path
):
    log_dir = tmp_path / ".config/cronboard/logs"
    job_dir = log_dir / "job1"
    log_dir.mkdir(parents=True)
    job_dir.mkdir()
    mocker.patch(f"{_LOGGER}.LOG_DIR", log_dir)
    keep = log_dir / "other_job_a.log"
    remove1 = job_dir / "job1_a.log"
    remove2 = job_dir / "job1_b.log"
    for p in (keep, remove1, remove2):
        p.write_text("x", encoding="utf-8")

    delete_logs_for_identificator("job1", ssh=None)

    assert not remove1.exists()
    assert not remove2.exists()
    assert keep.exists()


def test_delete_logs_for_identificator_local_noop_when_no_files(
    mocker: MockerFixture, tmp_path: Path
):
    mocker.patch(f"{_LOGGER}.LOG_DIR", tmp_path / ",config/cronboard/logs")
    (tmp_path / ".config/cronboard/logs").mkdir(parents=True)

    delete_logs_for_identificator("missing", ssh=None)


def test_delete_logs_for_identificator_remote_runs_rm(
    mocker: MockerFixture,
):
    ssh = ssh_mock_exec_sequence(
        mocker,
        [
            (b"/home/test\n", b""),
            (b"", b""),
        ],
    )

    delete_logs_for_identificator("app1", ssh=ssh)

    assert ssh.exec_command.call_count == 2
    rm_cmd = ssh.exec_command.call_args_list[1][0][0]
    assert rm_cmd.startswith("rm -rf -- ")
    assert "/home/test/.config/cronboard/logs/app1" in rm_cmd
