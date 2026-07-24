import pytest
from pytest_mock import MockerFixture
from cronboard.widgets.CronTable import CronTable


class TestCheckAction:
    """Actions are guarded by row count — empty tables disable navigation/search/edit."""

    guarded_actions = [
        "cron_search", "clear_search", "next_match", "prev_match",
        "edit_cronjob", "delete_cronjob", "pause_cronjob",
        "cursor_up", "cursor_down", "cursor_left", "cursor_right",
    ]
    free_actions = ["create_cronjob_keybind", "refresh", "view_logs"]

    def test_disabled_when_empty(self, empty_table: CronTable):
        for action in self.guarded_actions:
            assert empty_table.check_action(action, ()) is False

    def test_enabled_when_has_rows(self, table_with_rows: CronTable):
        all_actions = self.guarded_actions + self.free_actions
        for action in all_actions:
            assert table_with_rows.check_action(action, ()) is True

    def test_unknown_action_allowed(self, empty_table: CronTable):
        assert empty_table.check_action("some_unknown_action", ()) is True


class TestHighlightText:
    @pytest.mark.parametrize("text, query, expected", [
        ("hello world", "world", "world"),                 # middle match
        ("Hello World", "world", "World"),                 # case-insensitive match
        ("hello world", "xyz", "hello world"),             # no match — unchanged
        ("hello", "", "hello"),                            # empty query — unchanged
        ("", "hello", ""),                                 # empty text — unchanged
        ("foo bar foo baz", "foo", "foo"),                 # multiple matches
    ])
    def test_highlight_text(self, table: CronTable, text: str, query: str, expected: str):
        result = table._highlight_text(text, query)
        assert expected in str(result)


class TestApplySearch:
    def test_search_matches_identificator(self, table_with_data):
        table_with_data.apply_search("backup")
        assert table_with_data._search_query == "backup"
        assert table_with_data._search_matches == [0, 2]
        assert table_with_data._search_index == 0

    def test_search_matches_command(self, table_with_data):
        table_with_data.apply_search("cleanup")
        assert table_with_data._search_matches == [1]

    def test_search_case_insensitive(self, table_with_data):
        table_with_data.apply_search("BACKUP")
        assert table_with_data._search_matches == [0, 2]

    def test_search_no_match(self, table_with_data):
        table_with_data.apply_search("nonexistent")
        assert table_with_data._search_matches == []
        assert table_with_data._search_index == -1
        table_with_data.notify.assert_called_once()

    def test_empty_query_restores(self, table_with_data):
        table_with_data._search_matches = [0, 1]
        table_with_data.apply_search("")
        assert table_with_data._search_query == ""
        assert table_with_data._search_matches == []
        assert table_with_data._search_index == -1
        table_with_data._restore_cells.assert_called_once()


class TestSearchNavigation:
    def test_search_next_cycles_forward(self, table_with_matches):
        table_with_matches.action_search_next()
        assert table_with_matches._search_index == 1
        table_with_matches.move_cursor.assert_called_once_with(row=5)

        table_with_matches.action_search_next()
        assert table_with_matches._search_index == 2
        table_with_matches.move_cursor.assert_called_with(row=8)

        table_with_matches.action_search_next()
        assert table_with_matches._search_index == 0
        table_with_matches.move_cursor.assert_called_with(row=2)

    def test_search_prev_cycles_backward(self, table_with_matches):
        table_with_matches.action_search_prev()
        assert table_with_matches._search_index == 2
        table_with_matches.move_cursor.assert_called_once_with(row=8)

        table_with_matches.action_search_prev()
        assert table_with_matches._search_index == 1
        table_with_matches.move_cursor.assert_called_with(row=5)

        table_with_matches.action_search_prev()
        assert table_with_matches._search_index == 0
        table_with_matches.move_cursor.assert_called_with(row=2)

    def test_search_next_no_matches(self, table_no_matches):
        table_no_matches.action_search_next()
        assert table_no_matches._search_index == -1
        table_no_matches.move_cursor.assert_not_called()

    def test_search_prev_no_matches(self, table_no_matches):
        table_no_matches.action_search_prev()
        assert table_no_matches._search_index == -1
        table_no_matches.move_cursor.assert_not_called()


class TestClearSearch:
    def test_clears_all_search_state(self, table_with_search_state):
        table_with_search_state.action_clear_search()
        assert table_with_search_state._search_query == ""
        assert table_with_search_state._search_matches == []
        assert table_with_search_state._search_index == -1

    def test_restores_original_cells(self, table_with_search_state):
        table_with_search_state.action_clear_search()
        table_with_search_state._restore_cells.assert_called_once()


class TestFindIfCronjobExists:
    def test_finds_job_by_comment_and_command(self, table_and_job):
        table, _ = table_and_job
        result = table.find_if_cronjob_exists("test-job", "echo hello")
        assert result is not None
        assert result.comment == "test-job"

    def test_finds_job_with_wrapper_command(self, mocker: MockerFixture):
        table = CronTable()
        job = mocker.MagicMock()
        job.comment = "test-job"
        job.command = "WRAPPER_MARKER echo hello"
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([job])
        mocker.patch("cronboard.widgets.CronTable.has_wrapper", return_value=True)
        mocker.patch(
            "cronboard.widgets.CronTable.wrap_command",
            return_value="WRAPPER_MARKER echo hello",
        )
        mocker.patch(
            "cronboard.widgets.CronTable.command_without_wrapper",
            return_value="echo hello",
        )
        table.cron = cron
        table.remote = False
        table.ssh_client = None

        result = table.find_if_cronjob_exists("test-job", "echo hello")
        assert result == job

    def test_returns_none_when_no_match(self, mocker: MockerFixture):
        """Search terms don't match the job's comment or command."""
        table = CronTable()
        job = mocker.MagicMock()
        job.comment = "other-job"
        job.command = "echo other"
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([job])
        table.cron = cron
        table.remote = False
        table.ssh_client = None
        result = table.find_if_cronjob_exists("test-job", "echo hello")
        assert result is None

    def test_returns_none_when_empty_cron(self, mocker: MockerFixture):
        table = CronTable()
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([])
        table.cron = cron
        table.remote = False
        table.ssh_client = None
        result = table.find_if_cronjob_exists("test-job", "echo hello")
        assert result is None


class TestParseCron:
    """Cron parsing tests — build the table once per test since setup is extensive."""

    def _make_schedule(self, mocker, next_str, prev_str):
        """Helper to create a schedule mock with fixed strftime outputs."""
        schedule = mocker.MagicMock()
        schedule.get_next.return_value = mocker.MagicMock(
            strftime=lambda fmt: next_str
        )
        schedule.get_prev.return_value = mocker.MagicMock(
            strftime=lambda fmt: prev_str
        )
        return schedule

    def test_parses_active_job(self, mocker: MockerFixture):
        table = CronTable()
        job = mocker.MagicMock()
        job.slices.render.return_value = "* * * * *"
        job.command = "/usr/bin/test.sh"
        job.comment = "test-job"
        job.is_enabled.return_value = True
        job.schedule.return_value = self._make_schedule(mocker, "22.07.2026 at 12:00", "22.07.2026 at 11:00")
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([job])
        mocker.patch("cronboard.widgets.CronTable.has_wrapper", return_value=False)
        mocker.patch("cronboard.widgets.CronTable.command_without_wrapper", side_effect=lambda x: x)
        mocker.patch.object(table, "add_row")
        mocker.patch.object(table, "_restore_cells")
        mocker.patch.object(table, "_highlight_matches")
        mocker.patch.object(table, "move_cursor")
        mocker.patch.object(table, "update_cell_at")

        table.parse_cron(cron)

        table.add_row.assert_called_once()
        args, _ = table.add_row.call_args
        assert args[0] == "test-job"
        assert args[1] == "* * * * *"
        assert args[2] == "/usr/bin/test.sh"
        assert args[3] == "False"
        assert args[6] is not None  # Rich Text status

    def test_parses_paused_job(self, mocker: MockerFixture):
        table = CronTable()
        job = mocker.MagicMock()
        job.slices.render.return_value = "0 0 * * *"
        job.command = "/usr/bin/backup.sh"
        job.comment = "backup-job"
        job.is_enabled.return_value = False
        job.schedule.return_value = self._make_schedule(mocker, "23.07.2026 at 00:00", "22.07.2026 at 00:00")
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([job])
        mocker.patch("cronboard.widgets.CronTable.has_wrapper", return_value=True)
        mocker.patch("cronboard.widgets.CronTable.command_without_wrapper", side_effect=lambda x: x)
        mocker.patch.object(table, "add_row")
        mocker.patch.object(table, "_restore_cells")
        mocker.patch.object(table, "_highlight_matches")
        mocker.patch.object(table, "move_cursor")
        mocker.patch.object(table, "update_cell_at")

        table.parse_cron(cron)

        table.add_row.assert_called_once()
        args, _ = table.add_row.call_args
        assert args[0] == "backup-job"
        assert args[4] == "22.07.2026 at 00:00"  # last_dt
        assert args[5] == "Paused"  # next_dt is "Paused" when job is disabled

    def test_handles_schedule_error(self, mocker: MockerFixture):
        table = CronTable()
        job = mocker.MagicMock()
        job.slices.render.return_value = "bad-cron"
        job.command = "/usr/bin/test.sh"
        job.comment = "broken-job"
        job.is_enabled.return_value = True
        job.schedule.side_effect = ValueError("Invalid cron expression")
        cron = mocker.MagicMock()
        cron.__iter__.return_value = iter([job])
        mocker.patch("cronboard.widgets.CronTable.has_wrapper", return_value=False)
        mocker.patch("cronboard.widgets.CronTable.command_without_wrapper", side_effect=lambda x: x)
        mocker.patch.object(table, "add_row")
        mocker.patch.object(table, "_restore_cells")
        mocker.patch.object(table, "_highlight_matches")
        mocker.patch.object(table, "move_cursor")
        mocker.patch.object(table, "update_cell_at")

        table.parse_cron(cron)

        table.add_row.assert_called_once()
        args, _ = table.add_row.call_args
        assert "ERR:" in args[4]
        assert "ERR:" in args[5]
