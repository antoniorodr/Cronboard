import tomlkit
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Label

from cronboard.config import CRONBOARD_CONFIG_FILE
from cronboard.services.encryption.cron_encrypt import (
    decrypt_telegram_token,
    encrypt_telegram_token,
)


class CronSettings(Widget):
    """Settings panel for the CronBoard application.

    Attributes:
        cronboard_config: Path to the CronBoard config file.
    """

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        """Builds the settings panel: Telegram notification settings."""

        yield Vertical(
            Label("Telegram notifications", classes="settings-title"),
            Label("Enter your Telegram token", classes="form-label"),
            Input(
                placeholder="AAEFAAAAQKI_mDsJppSEQRr3kLOz9SatBxq48BgQLSHLRv;n",
                password=True,
                id="telegram-token",
            ),
            Label("Enter your Telegram chat ID", classes="form-label mt-2"),
            Input(placeholder="Chat ID", id="telegram-chat-id"),
            Horizontal(
                Button("Save", variant="primary", id="save"),
                id="button-row",
            ),
            id="settings-panel",
        )

    def on_mount(self) -> None:
        """Fetches the settings from the config file."""

        self.fetch_setting()

    def action_jump(self) -> None:
        """Jumps to the settings options."""

        settings_container: Input = self.query_one("#telegram-token", Input)
        if settings_container:
            settings_container.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Saves the settings."""

        telegram_token: str = self.query_one("#telegram-token", Input).value
        telegram_chat_id: str = self.query_one("#telegram-chat-id", Input).value

        if event.button.id == "save":
            try:
                config = tomlkit.loads(CRONBOARD_CONFIG_FILE.read_text())
                config["telegram_token"] = encrypt_telegram_token(telegram_token)
                config["telegram_chat_id"] = telegram_chat_id

                CRONBOARD_CONFIG_FILE.write_text(tomlkit.dumps(config))

                self.notify("Settings saved")
            except Exception as e:
                self.notify(f"Failed to save settings: {e}")

    def fetch_setting(self) -> None:
        """Fetches the settings from the config file."""

        try:
            with CRONBOARD_CONFIG_FILE.open("r") as f:
                config: dict = tomlkit.loads(f.read())
                telegram_token: str = config.get("telegram_token", "")
                telegram_chat_id: str = config.get("telegram_chat_id", "")
                self.query_one("#telegram-token", Input).value = decrypt_telegram_token(
                    telegram_token
                )
                self.query_one("#telegram-chat-id", Input).value = telegram_chat_id
        except Exception as e:
            print(f"Warning: Failed to fetch settings: {e}")
