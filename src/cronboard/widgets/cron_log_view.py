from __future__ import annotations

import re
from typing import ClassVar

from paramiko.client import SSHClient
from rich.cells import cell_len
from rich.style import Style
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Grid, Horizontal, Vertical
from textual.geometry import Offset, Size
from textual.message import Message
from textual.screen import ModalScreen
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button

from cronboard.services.cron_logging.logger import get_log_files, read_log_file

_sub_escape = re.compile("[\u0000-\u0014]").sub


def _process_log_line(line: str) -> str:
    return _sub_escape("", line.expandtabs())


_LOG_LIST_SELECTION_DEBOUNCE_SEC: float = 0.3


class VirtualLogFileList(ScrollView, can_focus=True):
    """Scrollable log file list: full list size for the scrollbar, one row rendered per screen line.

    Attributes:
        selected_index: Index of the selected log file.
    """

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
        self._keys: list[str] = keys
        self._paths: dict[str, str] = paths
        self._line_width: int = max((cell_len(k) for k in keys), default=1)
        self.selected_index: int = 0 if keys else -1
        self._selection_emit_timer: Timer | None = None

    def _cancel_selection_emit_timer(self) -> None:
        if self._selection_emit_timer is not None:
            self._selection_emit_timer.stop()
            self._selection_emit_timer = None

    def _schedule_emit_selected(self) -> None:
        self._cancel_selection_emit_timer()
        self._selection_emit_timer: Timer = self.set_timer(
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
        """Cancels the selection emit timer."""

        self._cancel_selection_emit_timer()

    def _refresh_dimensions(self) -> None:
        region_w: int = self.scrollable_content_region.width
        vw: int = max(self._line_width, region_w, 1)
        vh: int = max(1, len(self._keys) if self._keys else 1)
        self.virtual_size = Size(vw, vh)

    def on_resize(self, event: events.Resize) -> None:
        """Refreshes the dimensions of the widget."""

        self._refresh_dimensions()

    def on_mount(self) -> None:
        """Mounts the widget."""

        self._refresh_dimensions()
        if self._keys:
            self.selected_index: int = min(self.selected_index, len(self._keys) - 1)
            self._emit_selected_immediate()

    def _emit_selected(self) -> None:
        if not self._keys or self.selected_index < 0:
            return
        key: str = self._keys[self.selected_index]
        self.post_message(LogList.LogSelected(self._paths[key]))

    def _viewport_height(self) -> int:
        return max(1, self.scrollable_content_region.height)

    def _ensure_selection_visible(self) -> None:
        if not self._keys or self.selected_index < 0:
            return
        h: int = self._viewport_height()
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
        """Selects the previous log file."""

        if not self._keys:
            return
        if self.selected_index > 0:
            self.selected_index -= 1
            self._schedule_emit_selected()
            self._ensure_selection_visible()
            self.refresh()

    def action_select_cursor(self) -> None:
        """Selects the current log file."""

        self._emit_selected_immediate()

    def on_click(self, event: events.Click) -> None:
        """Handles click events.

        Args:
            event: events.Click object. Identifies the clicked position.
        """

        if not self._keys:
            return
        offset: Offset | None = event.get_content_offset(self)
        if offset is None:
            return
        row: int = int(self.scroll_offset.y) + offset.y
        if row < 0 or row >= len(self._keys):
            return
        event.stop()
        self.focus()
        self.selected_index: int = row
        self._emit_selected_immediate()
        self._ensure_selection_visible()
        self.refresh()

    def render_line(self, y: int) -> Strip:
        """Renders a line of the log file list.

        Args:
            y: Index of the line to render.

        Returns:
            A Strip object with the rendered line.
        """

        scroll_x, scroll_y = self.scroll_offset
        row: int = scroll_y + y
        width: int = self.size.width
        rich_style: Style = self.rich_style
        if not self._keys:
            if row != 0:
                return Strip.blank(width, rich_style)
            text = Text("No logs found", no_wrap=True)
            text.stylize(rich_style)
            return Strip(text.render(self.app.console), cell_len("No logs found"))
        if row >= len(self._keys):
            return Strip.blank(width, rich_style)
        label: str = self._keys[row]
        line_text = Text(label, no_wrap=True)
        line_text.stylize(rich_style)
        if row == self.selected_index:
            line_text.stylize(Style(reverse=True))
        strip = Strip(line_text.render(self.app.console), cell_len(label))
        strip: Strip = strip.crop_extend(scroll_x, scroll_x + width, rich_style)
        return strip.apply_offsets(scroll_x, scroll_y + y)


class VirtualLogLines(ScrollView, can_focus=True):
    """Scrollable log file body: all lines kept in memory; scrollbar reflects full height; only visible rows render."""

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
            head: list[str] = lines[:25_000]
            tail: list[str] = lines[-25_000:]
            max_w: int = max((cell_len(line) for line in head), default=1)
            return max(max_w, max((cell_len(line) for line in tail), default=1))
        return max((cell_len(line) for line in lines), default=1)

    def set_content(self, lines: list[str]) -> None:
        """Sets the content of the log file body.

        Args:
            lines: List of log lines.
        """

        self._lines: list[str] = [_process_log_line(line) for line in lines]
        self._max_cell_len: int = self._compute_max_cell_len(self._lines)
        self._apply_virtual_size()
        self.scroll_to(y=0.0, animate=False, immediate=True)
        self.refresh()

    def set_placeholder(self, message: str) -> None:
        """Sets the placeholder text for the log file body.

        Args:
            message: The placeholder text.
        """

        self._lines: list[str] = [_process_log_line(message)]
        self._max_cell_len: int = self._compute_max_cell_len(self._lines)
        self._apply_virtual_size()
        self.scroll_to(y=0.0, animate=False, immediate=True)
        self.refresh()

    def _apply_virtual_size(self) -> None:
        region_w: int = self.scrollable_content_region.width
        vw: int = max(self._max_cell_len, region_w, 1)
        vh: int = max(1, len(self._lines))
        self.virtual_size = Size(vw, vh)

    def on_resize(self, event: events.Resize) -> None:
        """Handles resize events."""

        if self._lines:
            self._apply_virtual_size()

    def render_line(self, y: int) -> Strip:
        """Renders a line of the log file body.

        Args:
            y: The index of the line to render.

        Returns:
            A Strip object with the rendered line.
        """

        scroll_x, scroll_y = self.scroll_offset
        row: int = scroll_y + y
        width: int = self.size.width
        rich_style: Style = self.rich_style
        if row >= len(self._lines):
            return Strip.blank(width, rich_style)
        raw: str = self._lines[row]
        line_text = Text(raw, no_wrap=True)
        line_text.stylize(rich_style)
        strip = Strip(line_text.render(self.app.console), cell_len(raw))
        strip: Strip = strip.crop_extend(scroll_x, scroll_x + width, rich_style)
        return strip.apply_offsets(scroll_x, scroll_y + y)


class LogList(Widget):
    """Log file list: list of log files with their full paths.

    Attributes:
        identificator: The identificator of the cronjob.
        log_paths: The dictionary of log files with their full paths.
        logs: The list of log files.
    """

    class LogSelected(Message):
        """Message posted when a log file is selected.

        Attributes:
            log_path: The full path of the selected log file.
        """

        def __init__(self, log_path: str) -> None:
            self.log_path: str = log_path
            super().__init__()

    def __init__(self, identificator: str, ssh_client=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identificator: str = identificator
        self.log_paths: dict = get_log_files(identificator, ssh_client)
        self.logs: list = list(self.log_paths.keys())

    def compose(self):
        yield VirtualLogFileList(self.logs, self.log_paths)


class LogView(Widget):
    """Log viewer: list of log files with their full paths, and a log file body.

    Attributes:
        ssh_client: Paramiko SSH client for remote operations.
        log_list: Log file list.
        log_output: The log file body.
    """

    BINDINGS = [
        Binding("l", "cursor_right", "Right"),
        Binding("h", "cursor_left", "Left"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
    ]

    def __init__(self, identificator: str, ssh_client=None) -> None:
        super().__init__()
        self.ssh_client: SSHClient | None = ssh_client
        self.log_list = LogList(
            identificator=identificator, id="log-list", ssh_client=ssh_client
        )
        self.log_output = VirtualLogLines(classes="focusable")

    def _file_list(self) -> VirtualLogFileList:
        return self.log_list.query_one(VirtualLogFileList)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Checks if the action is allowed.

        Args:
            action: The action to check.

        Returns:
            True if the action is allowed, else False.
        """

        is_empty: bool = not self.log_list.logs
        if action in (
            "cursor_up",
            "cursor_down",
            "cursor_left",
            "cursor_right",
        ):
            return not is_empty
        return True

    def action_cursor_left(self) -> None:
        """Selects the log file list."""

        self.app.set_focus(self._file_list())

    def action_cursor_right(self) -> None:
        """Selects the log file body."""

        self.app.set_focus(self.log_output)

    def action_cursor_down(self) -> None:
        """Scrolls down the log file body."""

        if self.log_output.has_focus:
            self.log_output.action_scroll_down()
            return
        if self.log_list.has_focus_within:
            self._file_list().action_cursor_down()

    def action_cursor_up(self) -> None:
        """Scrolls up the log file body."""

        if self.log_output.has_focus:
            self.log_output.action_scroll_up()
            return
        if self.log_list.has_focus_within:
            self._file_list().action_cursor_up()

    def compose(self) -> ComposeResult:
        """Builds the modal UI: log file list and log file body."""

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
        """Mounts the widget."""

        self.app.toggle_tab_enablement()  # Disable tab switching using the `Tab` key
        self.log_output.set_placeholder(
            "Please select a log from the list on the left."
        )

    def on_key(self, event: events.Key) -> None:
        """Handles key presses.

        Args:
            event: events.Key object. Identifies the key pressed.
        """

        if event.key == "tab":
            if isinstance(self.app.focused, VirtualLogFileList):
                self.app.set_focus(self.log_output)
            elif self.log_output.has_focus:
                self.query_one("#close", Button).focus()
            else:
                self.app.set_focus(self._file_list())

    @on(LogList.LogSelected)
    def show_log(self, event: LogList.LogSelected):
        """Shows the log file body.

        Args:
            event: LogList.LogSelected object. Identifies the selected log file.
        """

        lines: list[str] = read_log_file(event.log_path, self.ssh_client)
        if len(lines) == 0:
            self.log_output.set_content(["No logs found"])
        else:
            self.log_output.set_content(lines)


class LogViewModal(ModalScreen[bool]):
    """Modal screen for viewing a log file.

    Attributes:
        identificator: The identificator of the cronjob.
        ssh_client: Paramiko SSH client for remote operations.
    """

    def __init__(self, identificator: str, ssh_client=None):
        super().__init__()
        self.identificator: str = identificator
        self.ssh_client: SSHClient | None = ssh_client

    def compose(self) -> ComposeResult:
        """Builds the modal UI: log viewer."""

        yield Grid(
            LogView(identificator=self.identificator, ssh_client=self.ssh_client),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses."""

        self.app.toggle_tab_enablement()  # Enable tab switching using the `Tab` key
        self.dismiss(True)
