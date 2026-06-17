from textual.binding import Binding
from textual.widgets import Tree


class CronTree(Tree):
    BINDINGS = [Binding("j", "cursor_down", "Down"), Binding("k", "cursor_up", "Up")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
