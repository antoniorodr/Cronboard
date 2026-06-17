import pytest
from pytest_mock import MockerFixture
from tests.conftest import make_creator
from cronboard.screens.CronCreator import CronCreator
from cronboard.app import CronBoard
from cronboard.screens.CronCreator import CronAutoComplete


@pytest.mark.asyncio
async def test_open_create_cronjob_modal(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert isinstance(app.screen, CronCreator)


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
