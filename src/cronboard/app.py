import tomllib
from importlib.metadata import version, PackageNotFoundError
from crontab import CronTab
import tomlkit
from pathlib import Path
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import (
    Footer,
    Label,
    Tabs,
    Tab,
    Button,
    Input,
    Checkbox,
    MaskedInput,
    RadioButton,
    RadioSet,
    Select,
    Switch,
    TextArea,
)
from cronboard.widgets.CronTable import CronTable
from textual.containers import Container
from cronboard.widgets.CronTabs import CronTabs
from cronboard.screens.CronCreator import CronCreator
from cronboard.services.messages import CronJobDeleted
from cronboard.services.logging.logger import delete_logs_for_identificator
from cronboard.screens.CronDeleteConfirmation import CronDeleteConfirmation
from cronboard.screens.CronServers import CronServers


def is_form_element(element):
    return isinstance(
        element,
        (
            Input,
            Checkbox,
            Button,
            MaskedInput,
            RadioButton,
            RadioSet,
            Select,
            Switch,
            TextArea,
        ),
    )


class CronBoard(App):
    """A Textual App to manage cron jobs."""

    BASE_DIR = Path(__file__).resolve().parent
    CSS_PATH = BASE_DIR / "static" / "css" / "cronboard.tcss"

    BINDINGS = [
        Binding("q,ctrl+q", "quit", "Quit", priority=True),
        Binding("Tab", "next_tab_and_focus", "Change Tab"),
    ]

    def compose(self) -> ComposeResult:
        version = self.get_version()
        self.config_path = Path.home() / ".config/cronboard/config.toml"
        yield Label(
            f"""▄▖      ▄        ▌
▌ ▛▘▛▌▛▌▙▘▛▌▀▌▛▘▛▌
▙▖▌ ▙▌▌▌▙▘▙▌█▌▌ ▙▌ v{version}""",
            id="title",
        )
        yield Footer()
        self.tabs = CronTabs(
            Tab("Local", id="local"),
            Tab("Servers", id="servers"),
        )
        yield self.tabs
        self.content_container = Container(id="tab-content")
        yield self.content_container

    @on(CronJobDeleted)
    def _on_cron_job_deleted(self, event: CronJobDeleted) -> None:
        delete_logs_for_identificator(event.identificator, event.ssh_client)

    def on_mount(self) -> None:
        config = self.load_config()
        saved_theme = config.get("theme", "catppuccin-mocha")
        self.theme = saved_theme
        self.servers = None
        self.local_table = CronTable(id="local-crontable")
        self.content_container.mount(self.local_table)
        self.local_table.display = True
        self.set_focus(self.local_table)
        self.tab_disabled = False

    def load_config(self):
        if self.config_path.exists():
            try:
                with self.config_path.open("rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        return {}

    def watch_theme(self, theme: str):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with self.config_path.open("w") as f:
                f.write(tomlkit.dumps({"theme": theme}))
        except Exception as e:
            print(f"Warning: Failed to save theme: {e}")

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        tab_label = event.tab.label
        if tab_label == "Local":
            self.show_tab_content(0)
        elif tab_label == "Servers":
            self.show_tab_content(1)

    def show_tab_content(self, index: int) -> None:
        if index == 0:
            self.local_table.display = True
            if self.servers:
                self.servers.display = False
        elif index == 1:
            if not self.servers:
                self.servers = CronServers()
                self.content_container.mount(self.servers)
            self.local_table.display = False
            self.servers.display = True

    def toggle_tab_enablement(self):
        self.tab_disabled = not self.tab_disabled

    def on_key(self, event: events.Key) -> None:
        if event.key != "tab":
            return

        if self.tab_disabled:
            event.prevent_default()
            return

        if is_form_element(self.focused):
            return

        event.prevent_default()
        self.action_next_tab_and_focus()

    def action_next_tab_and_focus(self) -> None:
        tabs = self.tabs
        tab_widgets = list(tabs.query(Tab))
        tab_ids = [tab.id for tab in tab_widgets]
        current = tabs.active
        index = tab_ids.index(current)

        next_index = (index + 1) % len(tab_ids)
        next_tab_id = tab_ids[next_index]

        tabs.active = next_tab_id

        self.show_tab_content(next_index)
        self._focus_active_panel()

    def _focus_active_panel(self) -> None:
        if self.tabs.active == "local":
            if self.local_table:
                self.set_focus(self.local_table)

        elif self.tabs.active == "servers":
            if self.servers:
                self.servers.focus_tree()

    def action_create_cronjob(
        self, cron: CronTab, remote=False, ssh_client=None, crontab_user=None
    ) -> None:
        def check_save(save: bool | None) -> None:
            if save:
                self.local_table.action_refresh()
                if (
                    self.servers
                    and hasattr(self.servers, "current_cron_table")
                    and self.servers.current_cron_table
                ):
                    self.servers.current_cron_table.action_refresh()

        self.push_screen(
            CronCreator(
                cron, remote=remote, ssh_client=ssh_client, crontab_user=crontab_user
            ),
            check_save,
        )

    def action_delete_cronjob(
        self, job, cron=None, remote=False, ssh_client=None, crontab_user=None
    ) -> None:
        def check_delete(deleted: bool | None) -> None:
            if deleted:
                self.local_table.action_refresh()
                if (
                    self.servers
                    and hasattr(self.servers, "current_cron_table")
                    and self.servers.current_cron_table
                ):
                    self.servers.current_cron_table.action_refresh()

        self.push_screen(
            CronDeleteConfirmation(
                job=job,
                cron=cron,
                remote=remote,
                ssh_client=ssh_client,
                crontab_user=crontab_user,
            ),
            check_delete,
        )

    def action_edit_cronjob(
        self,
        cron: CronTab,
        identificator: str,
        expression: str,
        command: str,
        remote=False,
        ssh_client=None,
        crontab_user=None,
    ) -> None:
        def check_save(save: bool | None) -> None:
            if save:
                self.local_table.action_refresh()
                if (
                    self.servers
                    and hasattr(self.servers, "current_cron_table")
                    and self.servers.current_cron_table
                ):
                    self.servers.current_cron_table.action_refresh()

        self.push_screen(
            CronCreator(
                cron,
                identificator=identificator,
                expression=expression,
                command=command,
                remote=remote,
                ssh_client=ssh_client,
                crontab_user=crontab_user,
            ),
            check_save,
        )

    def get_version(self):
        try:
            return version("cronboard")
        except PackageNotFoundError:
            return "Unknown"


def main():
    app = CronBoard()
    app.run()


if __name__ == "__main__":
    app = CronBoard()
    app.run()
