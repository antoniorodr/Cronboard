import crontab
from textual.app import ComposeResult
from crontab import CronTab
from textual import events
from textual.widgets import Button, Label, Input
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from cron_descriptor import Options, ExpressionDescriptor


# TODO: Autocompletion using https://github.com/darrenburns/textual-autocomplete

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
    def __init__(
        self,
        cron,
        expression=None,
        command=None,
        identificator=None,
        remote=False,
        ssh_client=None,
    ) -> None:
        super().__init__()
        self.expression = expression
        self.command = command
        self.identificator = identificator
        self.cron: CronTab = cron
        self.remote = remote
        self.ssh_client = ssh_client

    def compose(self) -> ComposeResult:
        yield Grid(
            Vertical(
                Label("Special characters:", id="label_special"),
                Label("* = any value", id="label_asterisk"),
                Label(", = value list separator", id="label_comma"),
                Label("- = range of values", id="label_dash"),
                Label("/ = step values", id="label_slash"),
                Label(
                    "Enter a valid cron expression (remember whitespaces):", id="label1"
                ),
                Label("Minute - Hour - Day - Month - Weekday", id="label2"),
                Input(
                    value="" if not self.expression else self.expression,
                    placeholder="* * * * *",
                    id="expression",
                ),
                Label("", id="label_desc"),
                Label("Enter the command to execute:", id="label3"),
                Input(
                    value="" if self.command is None else self.command,
                    placeholder="e.g., python3 /usr/bin/python</path/to/script.py>",
                    id="command",
                ),
                Label("Enter a identificator", id="label4"),
                Input(
                    value="" if self.identificator is None else self.identificator,
                    placeholder="e.g., backup-job-1",
                    id="identificator",
                ),
                Horizontal(
                    Button("Save", variant="primary", id="save"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                ),
                id="content",
            ),
            id="dialog",
        )

    def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.save_content()
        elif event.key == "escape":
            self.dismiss(False)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "expression":
            return

        label_desc = self.query_one("#label_desc", Label)
        expr = event.value.strip()
        self.expression_description(expr, label_desc)

        error_labels = self.query("#error")
        for label in error_labels:
            label.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.save_content()
        elif event.button.id == "cancel":
            self.dismiss(False)

    def save_content(self) -> None:
        identificator_input = self.query_one("#identificator", Input)
        expression_input = self.query_one("#expression", Input)
        command_input = self.query_one("#command", Input)
        expression = expression_input.value
        command = command_input.value
        identificator = identificator_input.value
        content = self.query_one("#content", Vertical)

        if not identificator:
            error_label = Label("Identificator cannot be empty.", id="error")
            content.mount(error_label)
            return

        try:
            job = self.find_if_cronjob_exists(identificator, command)

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
            if not self.query("#error"):
                error_label = Label(
                    "Invalid cron expression. Please try again.", id="error"
                )
                content.mount(error_label)

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
                stdin, _, stderr = self.ssh_client.exec_command("crontab -")
                stdin.write(new_crontab_content)
                stdin.channel.shutdown_write()

                exit_status = stdin.channel.recv_exit_status()
                errors = stderr.read().decode().strip()

                if errors or exit_status != 0:
                    raise Exception(f"Failed to write remote crontab: {errors}")

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
