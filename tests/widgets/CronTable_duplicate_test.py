"""Simple tests for duplicate cronjob functionality."""

from cronboard.widgets.CronTable import CronTable


def test_duplicate_binding_exists():
    """Verify 'd' keybinding is registered for duplicate."""
    binding_keys = [b.key for b in CronTable.BINDINGS]
    assert "d" in binding_keys


def test_duplicate_binding_calls_action():
    """Verify 'd' binding calls action_duplicate_cronjob."""
    binding = next(b for b in CronTable.BINDINGS if b.key == "d")
    assert binding.action == "duplicate_cronjob"


def test_action_duplicate_cronjob_method_exists():
    """Verify action_duplicate_cronjob method exists and is callable."""
    assert hasattr(CronTable, "action_duplicate_cronjob")
    assert callable(getattr(CronTable, "action_duplicate_cronjob"))


def test_duplicate_binding_label():
    """Verify 'd' binding has correct description."""
    binding = next(b for b in CronTable.BINDINGS if b.key == "d")
    assert binding.description == "Duplicate"
