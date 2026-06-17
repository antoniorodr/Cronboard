from textual.app import ComposeResult
from crontab import CronTab
from textual.widgets import Button, Label, Input, RadioButton, RadioSet
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from cron_descriptor import Options, ExpressionDescriptor
from cronboard.services.logging.cron_wrapper import (
    has_wrapper,
    wrap_command,
    command_without_wrapper,
)
from cronboard.widgets.VimKeysRadioSet import VimKeysRadioSet
from cronboard.services.CronAutoComplete import CronAutoComplete

CRON_ALIASES = {
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
    ) -> None:
        super().__init__()
        self.expression = expression
        self.command = command
        self.identificator = identificator
        self.log_enabled = has_wrapper(command) if command else False
        self.cron: CronTab = cron
        self.remote = remote
        self.ssh_client = ssh_client
        self.crontab_user = crontab_user

    def compose(self) -> ComposeResult:
        with Grid(id="dialog"):
            with Vertical(id="content"):
                yield Label("Special characters:", id="label_special")
                yield Label("* = any value", id="label_asterisk")
                yield Label(", = value list separator", id="label_comma")
                yield Label("- = range of values", id="label_dash")
                yield Label("/ = step values", id="label_slash")
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
                yield CronAutoComplete(target=command_input)
                yield Label(
                    "Enter an ID for the cron job", classes="form-label mt-2 pt-2"
                )
                yield Input(
                    value="" if self.identificator is None else self.identificator,
                    placeholder="e.g., backup-job-1",
                    id="identificator",
                )
                yield Label(
                    "Tick if you want to enable logging", classes="form-label mt-2 pt-2"
                )
                yield VimKeysRadioSet(
                    RadioButton("Enable logging", id="enable", value=self.log_enabled),
                    RadioButton(
                        "Disable logging", id="disable", value=not self.log_enabled
                    ),
                )
                yield Horizontal(
                    Button("Save", variant="primary", id="save"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                )
                yield Label("", id="error")

    async def action_close_modal(self):
        await self.dismiss(False)

    def _show_error(self, message: str):
        error_label = self.query_one("#error")
        error_label.update(message)
        error_label.add_class(self._ERROR_VISIBLE_CLASS)

    def _clear_error(self):
        error_label = self.query_one("#error")
        error_label.update("")
        error_label.remove_class(self._ERROR_VISIBLE_CLASS)

    def _has_error(self):
        error_label = self.query_one("#error")
        return error_label.has_class(self._ERROR_VISIBLE_CLASS)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._clear_error()
        if event.input.id == "identificator":
            ident = event.value.strip()
            if not ident:
                self._show_error("ID cannot be empty.")
                return

            if " " in ident:
                self._show_error("ID cannot contain spaces. e.g., backup_job_1")
                return

        if event.input.id != "expression":
            return

        label_desc = self.query_one("#label_desc", Label)
        expr = event.value.strip()
        self.expression_description(expr, label_desc)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed.id == "enable":
            self.log_enabled = True
        else:
            self.log_enabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "save":
            self.dismiss(False)
            return

        if self._has_error():
            return

        identificator_input = self.query_one("#identificator", Input)
        expression_input = self.query_one("#expression", Input)
        command_input = self.query_one("#command", Input)
        expression = expression_input.value
        command = command_input.value
        identificator = identificator_input.value

        if not identificator:
            self._show_error("ID cannot be empty.")
            return

        if " " in identificator:
            self._show_error("ID cannot contain spaces. e.g., backup_job_1")
            return

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
                    ),
                )
            if self.log_enabled:
                command = wrap_command(
                    command,
                    identificator,
                    self.ssh_client if self.remote and self.ssh_client else None,
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

            expr = CRON_ALIASES.get(expr, expr)

            options = Options()
            options.locale_code = "en"
            options.use_24hour_time_format = True
            desc = ExpressionDescriptor(expr, options).get_description()

            label_desc.update(desc)
            label_desc.remove_class("error")
            label_desc.add_class("success")
        except Exception:
            label_desc.update("Invalid cron expression")
            label_desc.remove_class("success")
            label_desc.add_class("error")

    def write_cron_changes(self):
        """Write cron changes to appropriate destination (local or remote)"""
        if self.remote and self.ssh_client:
            try:
                new_crontab_content = self.cron.render()
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

                if errors or exit_status != 0:
                    self.notify(f"Failed to write remote crontab: {errors}")

            except Exception as e:
                print(f"❌ Error writing remote crontab: {e}")
                raise
        else:
            self.cron.write()

    def find_if_cronjob_exists(self, identificator: str, cmd: str):
        for job in self.cron:
            if job.comment == identificator and job.command == cmd:
                return job
        return None
