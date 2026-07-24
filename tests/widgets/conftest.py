import pytest
from pytest_mock import MockerFixture
from unittest.mock import PropertyMock
from cronboard.widgets.CronTable import CronTable


@pytest.fixture
def table() -> CronTable:
    """A bare CronTable instance for tests that don't need special setup."""
    yield CronTable()


@pytest.fixture
def empty_table(mocker: MockerFixture) -> CronTable:
    """CronTable with row_count=0."""
    _table = CronTable()
    mocker.patch.object(CronTable, "row_count", new_callable=PropertyMock(return_value=0))
    yield _table


@pytest.fixture
def table_with_rows(mocker: MockerFixture) -> CronTable:
    """CronTable with row_count=3."""
    _table = CronTable()
    mocker.patch.object(CronTable, "row_count", new_callable=PropertyMock(return_value=3))
    yield _table


@pytest.fixture
def table_with_data(mocker: MockerFixture) -> CronTable:
    """CronTable with three rows of cron job data and patched methods."""
    _table = CronTable()
    _table._rows_data = [
        ("job-1", "* * * * *", "/usr/bin/backup.sh", "True",
         "22.07.2026 at 10:00", "22.07.2026 at 11:00", "Active"),
        ("job-2", "0 */2 * * *", "/usr/bin/cleanup.sh", "False",
         "22.07.2026 at 09:00", "22.07.2026 at 12:00", "Paused"),
        ("db-backup", "0 0 * * *", "/usr/bin/db_dump.sh", "True",
         "21.07.2026 at 00:00", "23.07.2026 at 00:00", "Active"),
    ]
    _table._search_matches = []
    _table._search_index = -1
    _table._search_query = ""
    mocker.patch.object(_table, "_restore_cells")
    mocker.patch.object(_table, "_highlight_matches")
    mocker.patch.object(_table, "move_cursor")
    mocker.patch.object(_table, "notify")
    mocker.patch.object(_table, "update_cell_at")
    mocker.patch.object(_table, "clear")
    yield _table


@pytest.fixture
def table_with_matches(mocker: MockerFixture) -> CronTable:
    """CronTable with pre-set search matches at rows 2, 5, 8."""
    _table = CronTable()
    _table._search_matches = [2, 5, 8]
    _table._search_index = 0
    mocker.patch.object(_table, "move_cursor")
    yield _table


@pytest.fixture
def table_no_matches(mocker: MockerFixture) -> CronTable:
    """CronTable with empty search state and no cursor moves."""
    _table = CronTable()
    _table._search_matches = []
    _table._search_index = -1
    mocker.patch.object(_table, "move_cursor")
    yield _table


@pytest.fixture
def table_with_search_state(mocker: MockerFixture) -> CronTable:
    """CronTable with active search state for clear-search tests."""
    _table = CronTable()
    _table._search_query = "backup"
    _table._search_matches = [0, 2]
    _table._search_index = 0
    mocker.patch.object(_table, "_restore_cells")
    yield _table


@pytest.fixture
def table_and_job(mocker: MockerFixture) -> tuple:
    """CronTable with one cron job (test-job/echo hello)."""
    _table = CronTable()
    job = mocker.MagicMock()
    job.comment = "test-job"
    job.command = "echo hello"
    cron = mocker.MagicMock()
    cron.__iter__.return_value = iter([job])
    _table.cron = cron
    _table.remote = False
    _table.ssh_client = None
    yield _table, job
