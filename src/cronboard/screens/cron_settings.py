import tomlkit
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label

from cronboard.config import CONFIG_REL_PATH
from cronboard.services.encryption.cron_encrypt import (
    decrypt_password,
    encrypt_password,
)


class CronSettings(Widget):
    """Widget showing a list of the servers added by the user.

    Attributes:
        servers: Dict with the all the servers.
        current_ssh_client: Paramiko SSH client for remote operations.
        current_cron_table: CronTable with the cronjobs for the selected server.
        current_server_name: Selected server name.
    """

    BINDINGS = [
        Binding("J", "jump", "Switch Panel"),
    ]

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        """Builds the modal UI: CronTree with the servers and a Label."""

        yield Label("Telegram notification")
        yield Grid(
            MaskedInput("Enter your Telegram token", id="telegram-token"),
            Input("Enter your Telegram chat ID", id="telegram-chat-id"),
            id="settings-grid",
        )

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.title = str(event.value)

    def action_jump(self) -> None:
        """Jumps to the settings options."""

        settings_container: MaskedInput = self.query_one("#telegram-token", MaskedInput)
        if settings_container:
            settings_container.focus()
