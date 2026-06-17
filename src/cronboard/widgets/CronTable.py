from crontab import CronTab
from textual.widgets import DataTable
from textual.binding import Binding
from textual.coordinate import Coordinate
from datetime import datetime
from rich.text import Text
from cronboard.screens.CronInputSearch import CronInputSearch
from cronboard.services.logging.cron_wrapper import (
    has_wrapper,
    wrap_command,
    command_without_wrapper,
)
from cronboard.widgets.LogView import LogViewModal


class CronTable(DataTable):
    BINDINGS = [
        Binding("/", "cron_search", "Search"),
        Binding("escape", "clear_search", "Clear Search"),
        Binding("n", "search_next", "Next Match"),
        Binding("N", "search_prev", "Prev Match"),
        Binding("l", "cursor_right", "Right"),
        Binding("h", "cursor_left", "Left"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
        Binding("c", "create_cronjob_keybind", "Create"),
        Binding("D", "delete_cronjob", "Delete"),
        Binding("r", "refresh", "Refresh"),
        Binding("p", "pause_cronjob", "Pause Toggle"),
        Binding("e", "edit_cronjob", "Edit"),
        Binding("L", "view_logs", "View Logs"),
    ]

    def __init__(self, remote=False, ssh_client=None, crontab_user=None, **kwargs):
        super().__init__(**kwargs)
        self.remote = remote
        self.ssh_client = ssh_client
        self.crontab_user = crontab_user
        self._rows_data: list[tuple] = []
        self._search_matches: list[int] = []
        self._search_index: int = -1
        self._search_query: str = ""

    def on_mount(self) -> None:
        self.cron: CronTab = CronTab(user=True)
        self.add_columns(
            "ID",
            "Expression",
            "Command",
            "Log Enabled",
            "Last Run",
            "Next Run",
            "Status",
        )

        if self.remote and self.ssh_client:
            crontab_cmd = (
                f"crontab -u {self.crontab_user} -l"
                if self.crontab_user
                else "crontab -l"
            )
            _, stdout, _ = self.ssh_client.exec_command(crontab_cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 1:
                self.crontab_content = ""
            else:
                self.crontab_content = stdout.read().decode() if stdout else ""

            self.ssh_cron: CronTab | None = CronTab(tab=self.crontab_content)
        else:
            self.ssh_cron = None

        self.load_crontabs()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""
        is_empty = self.row_count == 0

        if action in (
            "cron_search",
            "clear_search",
            "next_match",
            "prev_match",
            "edit_cronjob",
            "delete_cronjob",
            "pause_cronjob",
            "cursor_up",
            "cursor_down",
            "cursor_left",
            "cursor_right",
        ):
            return not is_empty
        return True

    def on_key(self, event):
        is_empty = self.row_count == 0
        if event.key == "space":
            self.notify(f"empty: {is_empty}")

    def parse_cron(self, cron):
        for job in cron:
            expr = job.slices.render()
            cmd = command_without_wrapper(job.command)
            log_enabled = has_wrapper(job.command)
            identificator = job.comment if job.comment else "No ID"
            try:
                active_status = "Active" if job.is_enabled() else "Paused"
                schedule = job.schedule(date_from=datetime.now())
                next_dt = (
                    schedule.get_next().strftime("%d.%m.%Y at %H:%M")
                    if active_status == "Active"
                    else "Paused"
                )
                last_dt = schedule.get_prev().strftime("%d.%m.%Y at %H:%M")

            except ValueError as e:
                next_dt = f"ERR: {e}"
                last_dt = f"ERR: {e}"
                active_status = "Inactive"

            if active_status == "Active":
                status_text = Text(active_status, style="#B8E7B8")
            elif active_status == "Paused":
                status_text = Text(active_status, style="#FF6F61")
            else:
                status_text = Text(active_status, style="#F6BF00")

            self.add_row(
                identificator,
                expr,
                cmd,
                str(log_enabled),
                str(last_dt),
                str(next_dt),
                status_text,
            )
            self._rows_data.append(
                (
                    identificator,
                    expr,
                    cmd,
                    str(log_enabled),
                    str(last_dt),
                    str(next_dt),
                    status_text,
                )
            )

    def load_crontabs(self):
        self.clear()
        self._rows_data = []
        self._search_matches = []
        self._search_index = -1
        self._search_query = ""

        if self.remote and self.ssh_client:
            self.parse_cron(self.ssh_cron)

        else:
            self.parse_cron(self.cron)

    def action_create_cronjob_keybind(self) -> None:
        """Handle create cronjob action by calling the main app's method."""
        used_cron = self.ssh_cron if self.remote and self.ssh_client else self.cron
        self.app.action_create_cronjob(
            used_cron,
            remote=self.remote,
            ssh_client=self.ssh_client,
            crontab_user=self.crontab_user,
        )

    def action_edit_cronjob_keybind(self, identificator, expression, command) -> None:
        used_cron = self.ssh_cron if self.remote and self.ssh_client else self.cron
        self.app.action_edit_cronjob(
            used_cron,
            identificator=identificator,
            expression=expression,
            command=command,
            remote=self.remote,
            ssh_client=self.ssh_client,
            crontab_user=self.crontab_user,
        )

    def action_delete_cronjob_keybind(self, job) -> None:
        used_cron = self.ssh_cron if self.remote and self.ssh_client else self.cron
        self.app.action_delete_cronjob(
            job,
            cron=used_cron,
            remote=self.remote,
            ssh_client=self.ssh_client,
            crontab_user=self.crontab_user,
        )

    def action_refresh(self) -> None:
        """Refresh the cronjob list."""
        if self.remote and self.ssh_client:
            crontab_cmd = (
                f"crontab -u {self.crontab_user} -l"
                if self.crontab_user
                else "crontab -l"
            )
            _, stdout, _ = self.ssh_client.exec_command(crontab_cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 1:
                self.crontab_content = ""
            else:
                self.crontab_content = stdout.read().decode() if stdout else ""

            self.ssh_cron = CronTab(tab=self.crontab_content)
        else:
            self.cron = CronTab(user=True)
        self.load_crontabs()
        self.refresh_bindings()

    def action_cron_search(self) -> None:

        def check_search(search_query: str | None) -> None:
            if search_query is not None:
                self.apply_search(search_query)

        self.app.push_screen(CronInputSearch(), check_search)

    def action_clear_search(self) -> None:
        self._search_query = ""
        self._search_matches = []
        self._search_index = -1
        self._restore_cells()

    def apply_search(self, query: str) -> None:
        self._search_query = query.lower() if query else ""
        self._search_matches = []

        if not self._search_query:
            self._restore_cells()
            return

        for i, row_data in enumerate(self._rows_data):
            identificator, expr, cmd = (
                str(row_data[0]),
                str(row_data[1]),
                str(row_data[2]),
            )
            if (
                self._search_query in identificator.lower()
                or self._search_query in expr.lower()
                or self._search_query in cmd.lower()
            ):
                self._search_matches.append(i)

        if self._search_matches:
            self._search_index = 0
            self._highlight_matches()
            self.move_cursor(row=self._search_matches[0])
            self.notify(
                f"{len(self._search_matches)} match(es) for '{self._search_query}'"
            )
        else:
            self._search_index = -1
            self.notify(f"No matches for '{self._search_query}'")

    def _highlight_text(self, text: str, query: str) -> Text:
        result = Text(text)
        q_lower = query.lower()
        idx = text.lower().find(q_lower)
        while idx >= 0:
            result.stylize("bold yellow", idx, idx + len(query))
            idx = text.lower().find(q_lower, idx + 1)
        return result

    def _highlight_matches(self) -> None:
        self._restore_cells()
        for i in self._search_matches:
            row_data = self._rows_data[i]
            for col_idx in range(3):
                text = str(row_data[col_idx])
                if self._search_query.lower() in text.lower():
                    self.update_cell_at(
                        Coordinate(i, col_idx),
                        self._highlight_text(text, self._search_query),
                    )

    def _restore_cells(self) -> None:
        for i, row_data in enumerate(self._rows_data):
            for col_idx in range(3):
                self.update_cell_at(Coordinate(i, col_idx), row_data[col_idx])

    def action_search_next(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self.move_cursor(row=self._search_matches[self._search_index])

    def action_search_prev(self) -> None:
        if not self._search_matches:
            return
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self.move_cursor(row=self._search_matches[self._search_index])

    def action_pause_cronjob(self) -> None:

        row = self.get_row_at(self.cursor_row)
        identificator = row[0]
        cmd = row[2]

        cron_to_use = self.ssh_cron if (self.remote and self.ssh_client) else self.cron

        job_to_toggle = self.find_if_cronjob_exists(identificator, cmd)

        if job_to_toggle is None:
            job_to_toggle = self.find_if_cronjob_exists(
                identificator,
                wrap_command(
                    cmd,
                    identificator,
                    self.ssh_client if self.remote and self.ssh_client else None,
                ),
            )

        if job_to_toggle is None:
            job_to_toggle = self.find_if_cronjob_exists(
                identificator, command_without_wrapper(cmd)
            )

        if job_to_toggle:
            job_to_toggle.enable(
                False
            ) if job_to_toggle.is_enabled() else job_to_toggle.enable(True)

            if self.remote and self.ssh_client:
                self.write_remote_crontab()
            else:
                cron_to_use.write()
            self.load_crontabs()

    def action_edit_cronjob(self) -> None:

        row = self.get_row_at(self.cursor_row)
        identificator = row[0]
        expr = row[1]
        cmd = row[2]

        job_to_edit = self.find_if_cronjob_exists(
            identificator,
            wrap_command(
                cmd,
                identificator,
                self.ssh_client if self.remote and self.ssh_client else None,
            ),
        )
        if job_to_edit:
            self.action_edit_cronjob_keybind(
                identificator,
                expr,
                wrap_command(
                    cmd,
                    identificator,
                    self.ssh_client if self.remote and self.ssh_client else None,
                ),
            )
            return

        if not job_to_edit:
            job_to_edit = self.find_if_cronjob_exists(identificator, cmd)
        if job_to_edit:
            self.action_edit_cronjob_keybind(identificator, expr, cmd)

    def action_delete_cronjob(self) -> None:
        """Delete the selected cronjob."""

        row = self.get_row_at(self.cursor_row)
        identificator = row[0]
        cmd = row[2]

        job_to_delete = self.find_if_cronjob_exists(identificator, cmd)

        if job_to_delete:
            self.action_delete_cronjob_keybind(job_to_delete)

    def find_if_cronjob_exists(self, identificator: str, cmd: str):
        cron_to_use = self.ssh_cron if (self.remote and self.ssh_client) else self.cron

        cmd_variants = {
            cmd,
            wrap_command(
                cmd,
                identificator,
                self.ssh_client if self.remote and self.ssh_client else None,
            ),
            command_without_wrapper(cmd),
        }

        for job in cron_to_use:
            if job.comment == identificator and job.command in cmd_variants:
                return job
        return None

    def action_disconnect_ssh(self) -> None:
        """Disconnect SSH connection and return to local cron tab."""
        if self.remote and self.ssh_client:
            self.app.action_disconnect_ssh()

    def write_remote_crontab(self):
        """Writes the current SSH cron table back to the remote server."""
        if not (self.remote and self.ssh_client and self.ssh_cron):
            return False

        try:
            new_crontab_content = self.ssh_cron.render()

            crontab_cmd = (
                f"crontab -u {self.crontab_user} -"
                if self.crontab_user
                else "crontab -"
            )
            stdin, _, stderr = self.ssh_client.exec_command(crontab_cmd)
            stdin.write(new_crontab_content)
            stdin.channel.shutdown_write()

            exit_status = stdin.channel.recv_exit_status()
            errors = stderr.read().decode().strip()

            if errors:
                print(f"❌ Failed to write remote crontab: {errors}")
                return False

            if exit_status != 0:
                print(f"❌ Command failed with exit status: {exit_status}")
                return False

            print("✅ Remote crontab updated successfully")
            return True

        except Exception as e:
            print(f"❌ Error writing remote crontab: {e}")
            return False

    def action_view_logs(self) -> None:
        """View logs for the selected cronjob."""

        row = self.get_row_at(self.cursor_row)
        identificator = row[0]

        self.app.push_screen(
            LogViewModal(
                identificator=identificator,
                ssh_client=self.ssh_client if self.remote and self.ssh_client else None,
            ),
        )
