import tomlkit
from cron_descriptor import ExpressionDescriptor, Options
from crontab import CronTab
from paramiko.client import SSHClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Input, Label, RadioButton, RadioSet

from cronboard.config import CRONBOARD_NOTIFICATIONS_FILE
from cronboard.services.cron_autocomplete import CronAutoComplete
from cronboard.services.cron_logging.cron_wrapper import (
    CONFIG_REL_PATH,
    _generate_notifications_config_for_server,
    command_without_wrapper,
    get_remote_home,
    wrap_command,
)
from cronboard.widgets.cron_vim_keys_radio_set import VimKeysRadioSet

CRON_ALIASES: dict[str, None | str] = {
    "@reboot": None,
    "@hourly": "0 * * * *",
    "@daily": "0 0 * * *",
    "@weekly": "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@midnight": "0 0 * * *",
}


class CronCreator(ModalScreen[bool]):
    """Modal screen for creating and editing cron jobs.

    Provides a form with fields for cron expression, command, job ID,
    and logging preference. Supports both local and remote (SSH) crontabs.

    Returns:
        True on successful save, False on cancel.

    Args:
        cron: CronTab instance to read/write jobs.
        expression: Pre-filled cron expression (e.g. "* * * * *").
        command: Pre-filled command string.
        identificator: Pre-filled job ID/comment.
        remote: Whether this is a remote crontab via SSH.
        ssh_client: Paramiko SSH client for remote operations.
        crontab_user: CronTab instance for remote user-specific crontabs.
    """

    BINDINGS = [Binding(key="escape", action="close_modal", description="Close")]
    _ERROR_VISIBLE_CLASS = "error-showing"

    def __init__(
        self,
        cron,
        expression=None,
        command=None,
        identificator=None,
        remote=False,
        ssh_client=None,
        crontab_user=None,
        server_name="local",
    ) -> None:
        super().__init__()
        self.expression: str | None = expression
        self.command: str | None = command
        self.identificator: str | None = identificator
        self.log_enabled: bool = False
        self.cron: CronTab = cron
        self.remote: bool = remote
        self.ssh_client: SSHClient | None = ssh_client
        self.crontab_user: CronTab | None = crontab_user
        self.notifications_enabled: bool = False
        self.server_name: str = server_name

    def compose(self) -> ComposeResult:
        """Builds the modal UI: cron expression help, expression input,
        command input with autocomplete, job ID input, logging toggle,
        save/cancel buttons, and error label."""

        with Vertical(id="dialog"):
            with Vertical(id="content"):
                yield Label("Special characters:", id="label_special")
                yield Grid(
                    Label("* = any value", id="label_asterisk"),
                    Label(", = value list separator", id="label_comma"),
                    Label("- = range of values", id="label_dash"),
                    Label("/ = step values", id="label_slash"),
                    id="cron-help-grid",
                )
                yield Label(
                    "Enter a valid cron expression (remember whitespaces):",
                    classes="form-label",
                )
                yield Label("Minute - Hour - Day - Month - Weekday", id="label2")
                yield Input(
                    value="" if not self.expression else self.expression,
                    placeholder="* * * * *",
                    id="expression",
                )
                yield Label("", id="label_desc")
                yield Label("Enter the command to execute:", classes="form-label mt-2")
                command_input = Input(
                    value=""
                    if self.command is None
                    else command_without_wrapper(self.command),
                    placeholder="e.g., python3 /usr/bin/python</path/to/script.py>",
                    id="command",
                )
                yield command_input
                yield CronAutoComplete(target=command_input, ssh_client=self.ssh_client)
                yield Label(
                    "Enter an ID for the cron job", classes="form-label mt-2 pt-2"
                )
                yield Input(
                    value="" if self.identificator is None else self.identificator,
                    placeholder="e.g., backup-job-1",
                    id="identificator",
                )
                yield Label(
                    "Tick if you want to enable logging/notifications",
                    classes="form-label mt-2 pt-2",
                )
                yield (
                    Horizontal(
                        VimKeysRadioSet(
                            RadioButton(
                                "Enable logging", id="enable", value=self.log_enabled
                            ),
                            RadioButton(
                                "Disable logging",
                                id="disable",
                                value=not self.log_enabled,
                            ),
                        ),
                        VimKeysRadioSet(
                            RadioButton(
                                "Enable notifications",
                                id="enable-notifications",
                                value=self.notifications_enabled,
                            ),
                            RadioButton(
                                "Disable notifications",
                                id="disable-notifications",
                                value=not self.notifications_enabled,
                            ),
                        ),
                    )
                )
                yield Horizontal(
                    Button("Save", variant="primary", id="save"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                )
                yield Label("", id="error")

    async def action_close_modal(self) -> None:
        """Dismiss the modal on close"""

        await self.dismiss(False)

    def _show_error(self, message: str) -> None:
        error_label: Widget = self.query_one("#error")
        error_label.update(message)
        error_label.add_class(self._ERROR_VISIBLE_CLASS)

    def _clear_error(self) -> None:
        error_label: Widget = self.query_one("#error")
        error_label.update("")
        error_label.remove_class(self._ERROR_VISIBLE_CLASS)

    def _has_error(self) -> bool:
        error_label: Widget = self.query_one("#error")
        return error_label.has_class(self._ERROR_VISIBLE_CLASS)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Updates the error label when the input is changed

        Args:
            event: Input.Changed object. Identifies the felt with the error throught id.
        """

        self._clear_error()
        if event.input.id == "identificator":
            ident: str = event.value.strip()
            if not ident:
                self._show_error("ID cannot be empty.")
                return

            if " " in ident:
                self._show_error("ID cannot contain spaces. e.g., backup_job_1")
                return

        if event.input.id != "expression":
            return

        label_desc: Label = self.query_one("#label_desc", Label)
        expr: str = event.value.strip()
        self.expression_description(expr, label_desc)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Enable/disable logs using radio buttons

        Args:
            event: RadioSet.Changed object. Identifies the button throught id.
        """

        if event.pressed.id == "enable":
            self.log_enabled = True
        elif event.pressed.id == "disable":
            self.log_enabled = False
        elif event.pressed.id == "enable-notifications":
            self.notifications_enabled = True
        elif event.pressed.id == "disable-notifications":
            self.notifications_enabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Determines the action on button pressed. It saves the cronjob on save. Shows
        errors if any.

        Args:
            event: Button.Pressed object. Identifies the button throught id.
        """

        if event.button.id != "save":
            self.dismiss(False)
            return

        if self._has_error():
            return

        identificator_input: Input = self.query_one("#identificator", Input)
        expression_input: Input = self.query_one("#expression", Input)
        command_input: Input = self.query_one("#command", Input)
        expression: str = expression_input.value
        command: str = command_input.value
        identificator: str = identificator_input.value

        if not identificator:
            self._show_error("ID cannot be empty.")
            return

        if " " in identificator:
            self._show_error("ID cannot contain spaces. e.g., backup_job_1")
            return

        self.save_job_settings(
            identificator, self.notifications_enabled, self.log_enabled
        )
        if self.remote and self.ssh_client:
            self.push_notifications_to_remote()

        try:
            job = self.find_if_cronjob_exists(
                identificator, command_without_wrapper(command)
            )
            if not job:
                job = self.find_if_cronjob_exists(
                    identificator,
                    wrap_command(
                        command,
                        identificator,
                        self.ssh_client if self.remote and self.ssh_client else None,
                        self.server_name,
                    ),
                )
            if self.log_enabled or self.notifications_enabled:
                command = wrap_command(
                    command,
                    identificator,
                    self.ssh_client if self.remote and self.ssh_client else None,
                    self.server_name,
                )
            if job:
                job.set_command(command)
                job.setall(expression)
                self.write_cron_changes()
            else:
                cron_job = self.cron.new(command=command, comment=identificator)
                cron_job.setall(expression)
                self.write_cron_changes()

            self.dismiss(True)

        except (ValueError, KeyError):
            self._show_error("Invalid cron expression. Please try again.")

    def expression_description(self, expr: str, label_desc: Label) -> None:
        """Parses the cron expression to natural language, updating the label for the
        user.

        Args:
            expr: String of the cron expression.
            label_desc: The label with the natural language description of the cron
            expression.

        Raises:
            ValueError: If the cron expression is invalid. It updates the label.
        """

        if not expr:
            label_desc.update("")
            label_desc.remove_class("success")
            label_desc.remove_class("error")
            return

        try:
            if expr == "@reboot":
                label_desc.update("Runs at system startup")
                label_desc.remove_class("error")
                label_desc.add_class("success")
                return

            if len(expr.split()) > 5:
                raise ValueError("Invalid cron expression")

            expr: str = CRON_ALIASES.get(expr, expr)

            options = Options()
            options.locale_code = "en"
            options.use_24hour_time_format = True
            desc: str = ExpressionDescriptor(expr, options).get_description()

            label_desc.update(desc)
            label_desc.remove_class("error")
            label_desc.add_class("success")
        except Exception:
            label_desc.update("Invalid cron expression")
            label_desc.remove_class("success")
            label_desc.add_class("error")

    def write_cron_changes(self) -> None:
        """Write cron changes to appropriate destination (local or remote)"""

        if self.remote and self.ssh_client:
            try:
                new_crontab_content = self.cron.render()
                crontab_cmd: str = (
                    f"crontab -u {self.crontab_user} -"
                    if self.crontab_user
                    else "crontab -"
                )
                stdin, _, stderr = self.ssh_client.exec_command(crontab_cmd)
                stdin.write(new_crontab_content)
                stdin.channel.shutdown_write()

                exit_status: str = stdin.channel.recv_exit_status()
                errors: str = stderr.read().decode().strip()

                if errors or exit_status != 0:
                    self.notify(f"Failed to write remote crontab: {errors}")

            except Exception as e:
                print(f"❌ Error writing remote crontab: {e}")
                raise
        else:
            self.cron.write()

    def find_if_cronjob_exists(self, identificator: str, cmd: str):
        """Search for a cronjob in the list.

        Args:
            identificator: String which identifies the cronjob.
            cmd: String representation of the command the cronjob executes.

        Returns:
            The cronjob if it was found or None if don't.

        """
        for job in self.cron:
            if job.comment == identificator and job.command == cmd:
                return job
        return None

    def save_job_settings(
        self, cron_name: str, notifications: bool, logging: bool
    ) -> None:
        """Saves the notification settings to the notifications file."""

        try:
            with CRONBOARD_NOTIFICATIONS_FILE.open("r") as f:
                config = tomlkit.loads(f.read())
        except FileNotFoundError:
            config = tomlkit.document()

        self._migrate_old_format(config)

        if self.server_name not in config or not isinstance(
            config[self.server_name], dict
        ):
            config[self.server_name] = tomlkit.table()
        config[self.server_name][cron_name] = tomlkit.table()
        config[self.server_name][cron_name]["notifications"] = notifications
        config[self.server_name][cron_name]["logging"] = logging

        with CRONBOARD_NOTIFICATIONS_FILE.open("w") as f:
            f.write(tomlkit.dumps(config))

    def _migrate_old_format(self, config) -> None:
        """Migrate old flat format (key = true) to new per-server format."""

        to_migrate = []
        for key, value in config.items():
            if isinstance(value, bool):
                to_migrate.append(key)
        for key in to_migrate:
            value = config.pop(key)
            if "local" not in config or not isinstance(config["local"], dict):
                config["local"] = tomlkit.table()
            config["local"][key] = tomlkit.table()
            config["local"][key]["notifications"] = value
            config["local"][key]["logging"] = False

    def push_notifications_to_remote(self) -> None:
        """Pushes the flattened notifications.toml to the remote server."""

        try:
            content = _generate_notifications_config_for_server(self.server_name)
            if content is None:
                return

            home = get_remote_home(self.ssh_client)
            if not home:
                return

            remote_path = f"{home}/{CONFIG_REL_PATH}/notifications.toml"
            sftp = self.ssh_client.open_sftp()
            with sftp.open(remote_path, "w") as f:
                f.write(content)
            sftp.close()
        except Exception as e:
            print(f"Warning: Failed to sync notifications.toml to remote: {e}")
