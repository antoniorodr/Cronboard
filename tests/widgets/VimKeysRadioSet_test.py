import pytest
from unittest.mock import MagicMock
from textual.app import App, ComposeResult
from textual.widgets import RadioButton

from cronboard.app import CronBoard
from cronboard.widgets.VimKeysRadioSet import VimKeysRadioSet
from cronboard.screens.CronCreator import CronCreator


class _RadioDemoApp(App[None]):
    def compose(self) -> ComposeResult:
        yield VimKeysRadioSet(
            RadioButton("A", id="a", value=True),
            RadioButton("B", id="b"),
        )


@pytest.mark.asyncio
async def test_vim_keys_radio_set_jk_cycles_selection():
    async with _RadioDemoApp().run_test() as pilot:
        radio = pilot.app.query_one(VimKeysRadioSet)
        pilot.app.set_focus(radio)
        assert radio.pressed_button is not None
        start_id = radio.pressed_button.id
        await pilot.press("j")
        assert radio.pressed_button.id != start_id
        await pilot.press("k")
        assert radio.pressed_button.id == start_id


@pytest.mark.asyncio
async def test_cron_creator_edit_modal_logging_disabled_radio_default():
    cron = MagicMock()
    cron.__iter__ = MagicMock(return_value=iter([]))

    class T(App):
        def compose(self) -> ComposeResult:
            yield CronCreator(
                cron,
                identificator="j1",
                expression="* * * * *",
                command="echo hello",
            )

    async with T().run_test() as pilot:
        await pilot.pause()
        radio = pilot.app.query_one(VimKeysRadioSet)
        enable = radio.query_one("#enable", RadioButton)
        disable = radio.query_one("#disable", RadioButton)
        assert enable.value is False and disable.value is True
        assert radio.pressed_button is disable


@pytest.mark.asyncio
async def test_cron_creator_radio_responds_to_jk(app: CronBoard):
    async with app.run_test() as pilot:
        await pilot.press("c")
        assert isinstance(pilot.app.screen, CronCreator)
        radio = pilot.app.screen.query_one(VimKeysRadioSet)
        radio.focus()
        before_sel = radio._selected
        await pilot.press("j")
        assert radio._selected != before_sel
        await pilot.press("k")
        assert radio._selected == before_sel
