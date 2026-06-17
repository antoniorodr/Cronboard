import pytest
from cronboard.app import CronBoard
from cronboard.services.messages import CronJobDeleted
from pytest_mock import MockerFixture
from textual.widgets import Tree

_APP = "cronboard.app"


@pytest.mark.asyncio
async def test_change_tab(app: CronBoard):
    async with app.run_test() as pilot:
        assert app.tabs.active == "local"

        await pilot.press("tab")
        await pilot.pause()

        assert app.tabs.active == "servers"
        assert app.servers is not None

        server_tree = app.servers.query_one("#servers-tree", Tree)
        assert server_tree.has_focus


@pytest.mark.asyncio
async def test_refresh_data(app: CronBoard):
    async with app.run_test() as pilot:
        initial_data = app.local_table
        await pilot.press("r")
        refreshed_data = app.local_table
        assert initial_data == refreshed_data


@pytest.mark.asyncio
async def test_quit_app(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("ctrl+q")
        assert app.is_running is False


@pytest.mark.asyncio
async def test_app_deletes_logs_on_cron_job_deleted_message(
    mocker: MockerFixture, app: CronBoard
):
    mock_delete = mocker.patch(f"{_APP}.delete_logs_for_identificator")

    async with app.run_test() as pilot:
        app.post_message(CronJobDeleted("job-x"))
        await pilot.pause()

    mock_delete.assert_called_once_with("job-x", None)
