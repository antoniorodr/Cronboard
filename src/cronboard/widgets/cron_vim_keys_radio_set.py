from __future__ import annotations

from textual.binding import Binding
from textual.events import Mount
from textual.widget import Widget
from textual.widgets import RadioButton, RadioSet


class VimKeysRadioSet(RadioSet):
    """A RadioSet with Vim-like keyboard navigation."""

    BINDINGS = [
        Binding("j", "next_button", "Down"),
        Binding("k", "previous_button", "Up"),
    ]

    def _on_mount(self, _: Mount) -> None:
        self.call_next(self._sync_selected_to_pressed_option)

    def _sync_selected_to_pressed_option(self) -> None:
        pressed_index: int = self.pressed_index
        if pressed_index >= 0:
            self._selected: int = pressed_index

    def action_next_button(self) -> None:
        """Selects the next button."""

        super().action_next_button()
        self._apply_keyboard_selection()

    def action_previous_button(self) -> None:
        """Selects the previous button."""

        super().action_previous_button()
        self._apply_keyboard_selection()

    def _apply_keyboard_selection(self) -> None:
        if self._selected is None:
            return
        button: Widget = self._nodes[self._selected]
        if not isinstance(button, RadioButton):
            return
        if self._pressed_button is None and any(
            b.value for b in self.query(RadioButton)
        ):
            return
        if not button.value:
            button.value = True
