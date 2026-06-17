from __future__ import annotations

import re
from typing import ClassVar

from rich.cells import cell_len
from rich.style import Style
from rich.text import Text

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Grid, Horizontal, Vertical
from textual.geometry import Size
from textual.message import Message
from textual.screen import ModalScreen
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button

from cronboard.services.logging.logger import get_log_files, read_log_file

_sub_escape = re.compile("[\u0000-\u0014]").sub


def _process_log_line(line: str) -> str:
    return _sub_escape("", line.expandtabs())


_LOG_LIST_SELECTION_DEBOUNCE_SEC = 0.3


class VirtualLogFileList(ScrollView, can_focus=True):
    """Scrollable log file list: full list size for the scrollbar, one row rendered per screen line."""

    ALLOW_MAXIMIZE = True

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up", "cursor_up", "Cursor up", show=False, priority=True),
        Binding("down", "cursor_down", "Cursor down", show=False, priority=True),
    ]

    def __init__(
        self,
        keys: list[str],
        paths: dict[str, str],
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._keys = keys
        self._paths = paths
        self._line_width = max((cell_len(k) for k in keys), default=1)
        self.selected_index = 0 if keys else -1
        self._selection_emit_timer: Timer | None = None

    def _cancel_selection_emit_timer(self) -> None:
        if self._selection_emit_timer is not None:
            self._selection_emit_timer.stop()
            self._selection_emit_timer = None

    def _schedule_emit_selected(self) -> None:
        self._cancel_selection_emit_timer()
        self._selection_emit_timer = self.set_timer(
            _LOG_LIST_SELECTION_DEBOUNCE_SEC,
            self._emit_selected_after_debounce,
            name="log-list-selection-debounce",
        )

    def _emit_selected_after_debounce(self) -> None:
        self._selection_emit_timer = None
        self._emit_selected()

    def _emit_selected_immediate(self) -> None:
        self._cancel_selection_emit_timer()
        self._emit_selected()

    def on_unmount(self) -> None:
        self._cancel_selection_emit_timer()

    def _refresh_dimensions(self) -> None:
        region_w = self.scrollable_content_region.width
        vw = max(self._line_width, region_w, 1)
        vh = max(1, len(self._keys) if self._keys else 1)
        self.virtual_size = Size(vw, vh)

    def on_resize(self, event: events.Resize) -> None:
        self._refresh_dimensions()

    def on_mount(self) -> None:
        self._refresh_dimensions()
        if self._keys:
            self.selected_index = min(self.selected_index, len(self._keys) - 1)
            self._emit_selected_immediate()

    def _emit_selected(self) -> None:
        if not self._keys or self.selected_index < 0:
            return
        key = self._keys[self.selected_index]
        self.post_message(LogList.LogSelected(self._paths[key]))

    def _viewport_height(self) -> int:
        return max(1, self.scrollable_content_region.height)

    def _ensure_selection_visible(self) -> None:
        if not self._keys or self.selected_index < 0:
            return
        h = self._viewport_height()
        sy = int(self.scroll_target_y)
        if self.selected_index < sy:
            self.scroll_to(y=float(self.selected_index), animate=False, immediate=True)
        elif self.selected_index >= sy + h:
            self.scroll_to(
                y=float(self.selected_index - h + 1),
                animate=False,
                immediate=True,
            )

    def action_cursor_down(self) -> None:
        if not self._keys:
            return
        if self.selected_index < len(self._keys) - 1:
            self.selected_index += 1
            self._schedule_emit_selected()
            self._ensure_selection_visible()
            self.refresh()

    def action_cursor_up(self) -> None:
        if not self._keys:
            return
        if self.selected_index > 0:
            self.selected_index -= 1
            self._schedule_emit_selected()
            self._ensure_selection_visible()
            self.refresh()

    def action_select_cursor(self) -> None:
        self._emit_selected_immediate()

    def on_click(self, event: events.Click) -> None:
        if not self._keys:
            return
        offset = event.get_content_offset(self)
        if offset is None:
            return
        row = int(self.scroll_offset.y) + offset.y
        if row < 0 or row >= len(self._keys):
            return
        event.stop()
        self.focus()
        self.selected_index = row
        self._emit_selected_immediate()
        self._ensure_selection_visible()
        self.refresh()

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        row = scroll_y + y
        width = self.size.width
        rich_style = self.rich_style
        if not self._keys:
            if row != 0:
                return Strip.blank(width, rich_style)
            text = Text("No logs found", no_wrap=True)
            text.stylize(rich_style)
            return Strip(text.render(self.app.console), cell_len("No logs found"))
        if row >= len(self._keys):
            return Strip.blank(width, rich_style)
        label = self._keys[row]
        line_text = Text(label, no_wrap=True)
        line_text.stylize(rich_style)
        if row == self.selected_index:
            line_text.stylize(Style(reverse=True))
        strip = Strip(line_text.render(self.app.console), cell_len(label))
        strip = strip.crop_extend(scroll_x, scroll_x + width, rich_style)
        return strip.apply_offsets(scroll_x, scroll_y + y)


class VirtualLogLines(ScrollView, can_focus=True):
    """Log file body: all lines kept in memory; scrollbar reflects full height; only visible rows render."""

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._lines: list[str] = []
        self._max_cell_len = 1

    def _compute_max_cell_len(self, lines: list[str]) -> int:
        if not lines:
            return 1
        if len(lines) > 50_000:
            head = lines[:25_000]
            tail = lines[-25_000:]
            max_w = max((cell_len(line) for line in head), default=1)
            return max(max_w, max((cell_len(line) for line in tail), default=1))
        return max((cell_len(line) for line in lines), default=1)

    def set_content(self, lines: list[str]) -> None:
        self._lines = [_process_log_line(line) for line in lines]
        self._max_cell_len = self._compute_max_cell_len(self._lines)
        self._apply_virtual_size()
        self.scroll_to(y=0.0, animate=False, immediate=True)
        self.refresh()

    def set_placeholder(self, message: str) -> None:
        self._lines = [_process_log_line(message)]
        self._max_cell_len = self._compute_max_cell_len(self._lines)
        self._apply_virtual_size()
        self.scroll_to(y=0.0, animate=False, immediate=True)
        self.refresh()

    def _apply_virtual_size(self) -> None:
        region_w = self.scrollable_content_region.width
        vw = max(self._max_cell_len, region_w, 1)
        vh = max(1, len(self._lines))
        self.virtual_size = Size(vw, vh)

    def on_resize(self, event: events.Resize) -> None:
        if self._lines:
            self._apply_virtual_size()

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        row = scroll_y + y
        width = self.size.width
        rich_style = self.rich_style
        if row >= len(self._lines):
            return Strip.blank(width, rich_style)
        raw = self._lines[row]
        line_text = Text(raw, no_wrap=True)
        line_text.stylize(rich_style)
        strip = Strip(line_text.render(self.app.console), cell_len(raw))
        strip = strip.crop_extend(scroll_x, scroll_x + width, rich_style)
        return strip.apply_offsets(scroll_x, scroll_y + y)


class LogList(Widget):
    class LogSelected(Message):
        def __init__(self, log_path: str) -> None:
            self.log_path = log_path
            super().__init__()

    def __init__(self, identificator: str, ssh_client=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identificator = identificator
        self.log_paths = get_log_files(identificator, ssh_client)
        self.logs = list(self.log_paths.keys())

    def compose(self):
        yield VirtualLogFileList(self.logs, self.log_paths)


class LogView(Widget):
    BINDINGS = [
        Binding("l", "cursor_right", "Right"),
        Binding("h", "cursor_left", "Left"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
    ]

    def __init__(self, identificator: str, ssh_client=None) -> None:
        super().__init__()
        self.ssh_client = ssh_client
        self.log_list = LogList(
            identificator=identificator, id="log-list", ssh_client=ssh_client
        )
        self.log_output = VirtualLogLines(classes="focusable")

    def _file_list(self) -> VirtualLogFileList:
        return self.log_list.query_one(VirtualLogFileList)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        is_empty = not self.log_list.logs
        if action in (
            "cursor_up",
            "cursor_down",
            "cursor_left",
            "cursor_right",
        ):
            return not is_empty
        return True

    def action_cursor_left(self) -> None:
        self.app.set_focus(self._file_list())

    def action_cursor_right(self) -> None:
        self.app.set_focus(self.log_output)

    def action_cursor_down(self) -> None:
        if self.log_output.has_focus:
            self.log_output.action_scroll_down()
            return
        if self.log_list.has_focus_within:
            self._file_list().action_cursor_down()

    def action_cursor_up(self) -> None:
        if self.log_output.has_focus:
            self.log_output.action_scroll_up()
            return
        if self.log_list.has_focus_within:
            self._file_list().action_cursor_up()

    def compose(self) -> ComposeResult:
        with Vertical(id="content"):
            yield Horizontal(
                self.log_list,
                self.log_output,
                id="main",
            )
            yield Horizontal(
                Button("Close", variant="error", id="close"),
                id="button-row",
            )

        self.log_output.styles.width = "70%"
        self.log_list.styles.width = "30%"

    def on_mount(self) -> None:
        self.app.toggle_tab_enablement()  # Disable tab switching using the `Tab` key
        self.log_output.set_placeholder(
            "Please select a log from the list on the left."
        )

    def on_key(self, event: events.Key) -> None:
        if event.key == "tab":
            if isinstance(self.app.focused, VirtualLogFileList):
                self.app.set_focus(self.log_output)
            elif self.log_output.has_focus:
                self.query_one("#close", Button).focus()
            else:
                self.app.set_focus(self._file_list())

    @on(LogList.LogSelected)
    def show_log(self, event: LogList.LogSelected):
        lines = read_log_file(event.log_path, self.ssh_client)
        if len(lines) == 0:
            self.log_output.set_content(["No logs found"])
        else:
            self.log_output.set_content(lines)


class LogViewModal(ModalScreen[bool]):
    def __init__(self, identificator: str, ssh_client=None):
        super().__init__()
        self.identificator = identificator
        self.ssh_client = ssh_client

    def compose(self) -> ComposeResult:
        yield Grid(
            LogView(identificator=self.identificator, ssh_client=self.ssh_client),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.toggle_tab_enablement()  # Enable tab switching using the `Tab` key
        self.dismiss(True)
