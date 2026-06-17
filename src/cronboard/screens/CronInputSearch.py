from textual.widgets import Input
from textual.binding import Binding
from textual.app import ComposeResult
from textual.screen import ModalScreen


class CronInputSearch(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel_search", "Cancel Search"),
    ]

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type to search cronjobs....", id="cron-search-input")

    def action_cancel_search(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)
