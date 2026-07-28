import pytest
from pytest_mock import MockerFixture
from textual.widgets import RadioButton

from cronboard.app import CronBoard
from cronboard.screens.cron_creator import CronAutoComplete, CronCreator
from tests.conftest import make_creator


@pytest.mark.asyncio
async def test_open_create_cronjob_modal(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert isinstance(app.screen, CronCreator)


@pytest.mark.asyncio
async def test_notifications_radio_updates_the_modal(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("c")
        screen: CronCreator = app.screen

        assert screen.query_one("#enable-notifications", RadioButton).value is True

        screen.query_one("#disable-notifications", RadioButton).value = True
        await pilot.pause()

        assert screen.notifications is False
        assert screen.log_enabled is False


def test_returns_job_when_match(mocker: MockerFixture):
    job = mocker.MagicMock()
    job.comment = "backup-job"
    job.command = "/usr/bin/backup.sh"

    creator = make_creator(mocker)
    creator.cron.__iter__ = mocker.MagicMock(return_value=iter([job]))
    result = creator.find_if_cronjob_exists("backup-job", "/usr/bin/backup.sh")
    assert result == job


def test_returns_none_when_no_match(mocker: MockerFixture):
    creator = make_creator(mocker)
    result = creator.find_if_cronjob_exists(
        "nonexistent-job", "/usr/bin/nonexistent.sh"
    )
    assert result is None


def test_returns_none_when_only_comment_matches(mocker: MockerFixture):
    job = mocker.MagicMock()
    job.comment = "backup-job"
    job.command = "/other/cmd"

    creator = make_creator(mocker)
    creator.cron.__iter__ = mocker.MagicMock(return_value=iter([job]))

    result = creator.find_if_cronjob_exists("backup-job", "/usr/bin/backup.sh")
    assert result is None


def test_returns_job_when_only_the_wrapper_differs(mocker: MockerFixture):
    job = mocker.MagicMock()
    job.comment = "backup-job"
    job.command = (
        "/bin/bash /tmp/cron-wrapper.sh backup-job --no-notify "
        "cronboard1:ZWNobyBoZWxsbw=="
    )

    creator = make_creator(mocker)
    creator.cron.__iter__ = mocker.MagicMock(return_value=iter([job]))

    result = creator.find_if_cronjob_exists("backup-job", "echo hello")
    assert result == job


def test_notifications_enabled_by_default(mocker: MockerFixture):
    creator = make_creator(mocker)
    assert creator.notifications is True


def test_notifications_disabled_when_command_has_the_flag(mocker: MockerFixture):
    creator = make_creator(
        mocker,
        command=(
            "/bin/bash /tmp/cron-wrapper.sh backup-job --no-notify "
            "cronboard1:ZWNobyBoZWxsbw=="
        ),
    )
    assert creator.notifications is False


def test_get_search_string_no_slash(
    mocker: MockerFixture, autocomplete: CronAutoComplete
):
    state = mocker.MagicMock()
    state.text = "python3"
    state.cursor_position = 7
    assert autocomplete.get_search_string(state) == "python3"


def test_get_search_string_with_slash(
    mocker: MockerFixture, autocomplete: CronAutoComplete
):
    state = mocker.MagicMock()
    state.text = "/home/user/scri"
    state.cursor_position = 15
    assert autocomplete.get_search_string(state) == "scri"


def test_get_search_string_multiple_words(
    mocker: MockerFixture, autocomplete: CronAutoComplete
):
    state = mocker.MagicMock()
    state.text = "cp /home/user/fil"
    state.cursor_position = 17
    assert autocomplete.get_search_string(state) == "fil"
