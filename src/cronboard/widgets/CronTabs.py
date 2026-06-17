from textual.binding import Binding
from textual.widgets import Tabs


class CronTabs(Tabs):
    BINDINGS = [
        Binding(
            "l",
            "next_tab",
            "Right",
        ),
        Binding("h", "previous_tab", "Left"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
