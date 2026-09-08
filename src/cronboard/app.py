import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import tomlkit
from crontab import CronTab
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.content import Content
from textual.widget import Widget
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    MaskedInput,
    RadioButton,
    RadioSet,
    Select,
    Switch,
    Tab,
    Tabs,
    TextArea,
)

from cronboard.screens.cron_creator import CronCreator
from cronboard.screens.cron_delete_confirmation import CronDeleteConfirmation
from cronboard.screens.cron_servers import CronServers
from cronboard.screens.cron_settings import CronSettings
from cronboard.services.cron_logging.cron_logger import delete_logs_for_identificator
from cronboard.services.cron_messages import CronJobDeleted
from cronboard.themes.everforest_dark_hard import everforest_dark_hard
from cronboard.widgets.cron_table import CronTable
from cronboard.widgets.cron_tabs import CronTabs

# TODO: Add a way to configure the default theme


def is_form_element(element: Widget | None):
    """Checks if the element is a form element.

    Args:
        element: The element to check.

    Returns:
        True if the element is a form element, else False.
    """

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
    """A Textual App to manage cron jobs.

    Attributes:
        BASE_DIR: The base directory of the app.
        CSS_PATH: The path to the CSS file.
        config_path: The path to the config file.
        tabs: The CronTabs widget.
        content_container: The container for the tab content.
        theme: The theme to use.
        servers: The CronServers widget.
        local_table: The CronTable widget for the local crontab.
        display: The display state of the CronTable widget.
        tab_disabled: The disabled state of the tabs.
        active: The active tab.
    """

    BASE_DIR: Path = Path(__file__).resolve().parent
    CSS_PATH = BASE_DIR / "static" / "css" / "cronboard.tcss"

    BINDINGS = [
        Binding("q,ctrl+q", "quit", "Quit", priority=True),
        Binding("Tab", "next_tab_and_focus", "Change Tab"),
    ]

    def compose(self) -> ComposeResult:
        """Builds the UI: title, footer, tabs, and content container."""

        version: str = self.get_version()
        self.config_path: Path = Path.home() / ".config/cronboard/config.toml"
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
            Tab("Settings", id="settings"),
        )
        yield self.tabs
        self.content_container = Container(id="tab-content")
        yield self.content_container

    @on(CronJobDeleted)
    def _on_cron_job_deleted(self, event: CronJobDeleted) -> None:
        delete_logs_for_identificator(event.identificator, event.ssh_client)

    def on_mount(self) -> None:
        """Loads the theme and config, and mounts the CronTable widget."""

        self.register_theme(everforest_dark_hard)
        config: dict = self.load_config()
        saved_theme: str = config.get("theme", "catppuccin-mocha")
        self.theme: str = saved_theme
        self.servers = None
        self.settings_tab = None
        self.local_table = CronTable(id="local-crontable", server_name="local")
        self.content_container.mount(self.local_table)
        self.local_table.display = True
        self.set_focus(self.local_table)
        self.tab_disabled = False

    def load_config(self) -> dict:
        """Loads the config file.

        Returns:
            The config as a dictionary.
        """

        if self.config_path.exists():
            try:
                with self.config_path.open("rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        return {}

    def watch_theme(self, theme: str) -> None:
        """Watches the theme and saves it to the config file.

        Args:
            theme: The theme to watch.
        """

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = self.load_config()
            config["theme"] = theme
            with self.config_path.open("w") as f:
                f.write(tomlkit.dumps(config))
        except Exception as e:
            print(f"Warning: Failed to save theme: {e}")

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Shows the content for the activated tab.

        Args:
            event: Tabs.TabActivated object. Identifies the activated tab.
        """

        tab_label: Content = event.tab.label
        if tab_label == "Local":
            self.show_tab_content(0)
        elif tab_label == "Servers":
            self.show_tab_content(1)
        elif tab_label == "Settings":
            self.show_tab_content(2)

    def show_tab_content(self, index: int) -> None:
        """Shows the content for the tab at the given index.

        Args:
            index: The index of the tab.
        """

        if index == 0:
            self.local_table.display = True
            if self.servers:
                self.servers.display = False
            if self.settings_tab:
                self.settings_tab.display = False
        elif index == 1:
            if not self.servers:
                self.servers = CronServers()
                self.content_container.mount(self.servers)
            self.local_table.display = False
            self.servers.display = True
        elif index == 2:
            if self.servers:
                self.servers.display = False
            self.local_table.display = False
            if not self.settings_tab:
                self.settings_tab = CronSettings()
                self.content_container.mount(self.settings_tab)
            self.settings_tab.display = True

    def toggle_tab_enablement(self) -> None:
        self.tab_disabled: bool = not self.tab_disabled

    def on_key(self, event: events.Key) -> None:
        """Handles key presses.

        Args:
            event: events.Key object. Identifies the key pressed.
        """

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
        """Switches to the next tab and focuses the first form element."""

        tabs: CronTabs = self.tabs
        tab_widgets: list[Tab] = list(tabs.query(Tab))
        tab_ids: list[str] = [tab.id for tab in tab_widgets]
        current: str = tabs.active
        index: int = tab_ids.index(current)

        next_index: int = (index + 1) % len(tab_ids)
        next_tab_id: str = tab_ids[next_index]

        tabs.active = next_tab_id

        self.show_tab_content(next_index)
        self._focus_active_panel()

    def _focus_active_panel(self) -> None:
        if self.tabs.active == "local" and self.local_table:
            self.set_focus(self.local_table)

        elif self.tabs.active == "servers" and self.servers:
            self.servers.focus_tree()

        elif self.tabs.active == "settings" and self.settings_tab:
            self.settings_tab.action_jump()

    def action_create_cronjob(
        self,
        cron: CronTab,
        remote=False,
        ssh_client=None,
        crontab_user=None,
        server_name="local",
    ) -> None:
        """Shows the CronCreator modal.

        Args:
            remote: The remote crontab.
            ssh_client: Paramiko SSH client for remote operations.
            crontab_user: The CronTab user for the remote server.
            cron: The CronTab instance to create.
        """

        def check_save(save: bool | None) -> None:
            """Callback for the save button.

            Args:
                save: The save state.
            """

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
                remote=remote,
                ssh_client=ssh_client,
                crontab_user=crontab_user,
                server_name=server_name,
            ),
            check_save,
        )

    def action_delete_cronjob(
        self,
        job,
        cron=None,
        remote=False,
        ssh_client=None,
        crontab_user=None,
        server_name="local",
    ) -> None:
        """Shows the CronDeleteConfirmation modal.

        Args:
            job: The CronJob to delete.
            cron: The CronTab instance to delete.
            remote: The remote crontab.
            ssh_client: Paramiko SSH client for remote operations.
            crontab_user: The CronTab user for the remote server.
        """

        def check_delete(deleted: bool | None) -> None:
            """Callback for the delete button.

            Args:
                deleted: The delete state.
            """

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
                server_name=server_name,
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
        server_name="local",
    ) -> None:
        """Shows the CronCreator modal to edit a cronjob.

        Args:
            remote: The remote crontab.
            ssh_client: Paramiko SSH client for remote operations.
            crontab_user: The CronTab user for the remote server.
            cron: The CronTab instance to edit.
            identificator: The identificator of the cronjob.
            expression: The cron expression.
            command: The command to execute.
        """

        def check_save(save: bool | None) -> None:
            """Callback for the save button.

            Args:
                save: The save state.
            """

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
                server_name=server_name,
            ),
            check_save,
        )

    def get_version(self) -> str:
        """Gets the version of the app.

        Returns:
            The version of the app. If not found, returns "Unknown".
        """

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
