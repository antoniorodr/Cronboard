from types import SimpleNamespace
import pytest
from pytest_mock import MockerFixture
from tests.conftest import create_event, create_content, make_query_one
from cronboard.screens.CronSSHModal import CronSSHModal
from textual.containers import Grid


def test_parse_host_info_defaults_port():
    hostname, port = CronSSHModal._parse_host_info("node9")
    assert hostname == "node9"
    assert port == 22


def test_parse_host_info_with_port():
    hostname, port = CronSSHModal._parse_host_info("node9:2222")
    assert hostname == "node9"
    assert port == 2222


def test_parse_host_info_strips_whitespace():
    hostname, port = CronSSHModal._parse_host_info("  node9:2222  ")
    assert hostname == "node9"
    assert port == 2222


@pytest.mark.parametrize(
    "value",
    ["", ":", "node9:", ":2222", "node9:abc", "node9:0", "node9:70000"],
)
def test_parse_host_info_invalid(value):
    with pytest.raises(ValueError):
        CronSSHModal._parse_host_info(value)


def test_compose_builds_dialog(modal: CronSSHModal):
    widgets = list(modal.compose())

    assert len(widgets) == 1
    assert isinstance(widgets[0], Grid)
    assert widgets[0].id == "dialog"


def test_on_input_changed_removes_existing_errors(
    mocker: MockerFixture, modal: CronSSHModal
):
    error_one = mocker.MagicMock()
    error_two = mocker.MagicMock()
    modal.query = mocker.Mock(side_effect=[[error_one], [error_one, error_two]])
    modal.query_one = mocker.Mock(return_value=error_one)
    event = mocker.MagicMock()

    modal.on_input_changed(event)

    error_one.remove.assert_called()
    error_two.remove.assert_called_once_with()


def test_on_button_pressed_cancel_dismisses_false(
    mocker: MockerFixture, modal: CronSSHModal
):
    modal.dismiss = mocker.Mock()
    event = create_event("cancel")

    modal.on_button_pressed(event)

    modal.dismiss.assert_called_once_with(False)


def test_on_button_pressed_add_dismisses_server_data(
    mocker: MockerFixture, modal: CronSSHModal
):
    modal.dismiss = mocker.Mock()
    modal.query = mocker.Mock(return_value=[])
    content = create_content(mocker)
    modal.query_one = make_query_one(
        {
            "#hostname": SimpleNamespace(value=" node9:2222 "),
            "#username": SimpleNamespace(value=" test "),
            "#password": SimpleNamespace(value=" password "),
            "#crontab_user": SimpleNamespace(value=" root "),
            "#content": content,
        }
    )
    event = create_event("add")

    modal.on_button_pressed(event)

    modal.dismiss.assert_called_once_with(
        {
            "hostname": "node9",
            "port": 2222,
            "username": "test",
            "password": "password",
            "ssh_key": False,
            "crontab_user": "root",
        }
    )
    content.mount.assert_not_called()


def test_on_button_pressed_add_uses_ssh_key_when_password_is_empty(
    mocker: MockerFixture, modal: CronSSHModal
):
    modal.dismiss = mocker.Mock()
    modal.query = mocker.Mock(return_value=[])
    content = create_content(mocker)
    modal.query_one = make_query_one(
        {
            "#hostname": SimpleNamespace(value="node9"),
            "#username": SimpleNamespace(value="test"),
            "#password": SimpleNamespace(value=""),
            "#crontab_user": SimpleNamespace(value=""),
            "#content": content,
        }
    )
    event = create_event("add")

    modal.on_button_pressed(event)

    modal.dismiss.assert_called_once_with(
        {
            "hostname": "node9",
            "port": 22,
            "username": "test",
            "password": "",
            "ssh_key": True,
            "crontab_user": None,
        }
    )


def test_on_button_pressed_does_not_duplicate_existing_error(
    mocker: MockerFixture, modal: CronSSHModal
):
    modal.dismiss = mocker.Mock()
    content = create_content(mocker)
    modal.query = mocker.Mock(return_value=[mocker.MagicMock()])
    modal.query_one = make_query_one(
        {
            "#hostname": SimpleNamespace(value=":"),
            "#username": SimpleNamespace(value="alice"),
            "#password": SimpleNamespace(value=""),
            "#crontab_user": SimpleNamespace(value=""),
            "#content": content,
        }
    )
    event = create_event("add")

    modal.on_button_pressed(event)

    content.mount.assert_not_called()
    modal.dismiss.assert_not_called()
