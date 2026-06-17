import pytest
from cronboard.screens.CronInputSearch import CronInputSearch
from textual.pilot import Pilot


async def search_input(pilot: Pilot):
    await pilot.press("/")
    await pilot.press("c")
    await pilot.press("r")
    await pilot.press("o")
    await pilot.press("n")
    await pilot.press("enter")


@pytest.mark.asyncio
async def test_open_search_modal(pilot: Pilot):
    await pilot.press("/")
    assert isinstance(pilot.app.screen, CronInputSearch)


@pytest.mark.asyncio
async def test_close_search_modal(pilot: Pilot):
    await pilot.press("/")
    await pilot.press("escape")
    assert not isinstance(pilot.app.screen, CronInputSearch)


@pytest.mark.asyncio
async def test_search_input(pilot: Pilot):
    crontable = pilot.app.query_one("#local-crontable")
    await search_input(pilot)
    assert crontable._search_query == "cron"


@pytest.mark.asyncio
async def test_clean_search_query(pilot: Pilot):
    crontable = pilot.app.query_one("#local-crontable")
    await search_input(pilot)
    await pilot.press("escape")
    assert crontable._search_query == ""
