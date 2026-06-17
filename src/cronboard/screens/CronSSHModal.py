from textual.app import ComposeResult
from textual.widgets import Button, Label, Input
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen


class CronSSHModal(ModalScreen):
    @staticmethod
    def _parse_host_info(host_info: str) -> tuple[str, int]:
        host_info = host_info.strip()
        if not host_info:
            raise ValueError("Empty host")

        if ":" in host_info:
            hostname, port_str = host_info.rsplit(":", 1)
            if not hostname or not port_str:
                raise ValueError("Invalid host format")
            try:
                port = int(port_str)
            except ValueError as exc:
                raise ValueError("Invalid port") from exc
            if port < 1 or port > 65535:
                raise ValueError("Invalid port")
            return hostname, port

        return host_info, 22

    def compose(self) -> ComposeResult:
        yield Grid(
            Vertical(
                Label(
                    "Add a remote server into the tree view",
                    id="label1",
                ),
                Input(
                    placeholder="Hostname (e.g. localhost or localhost:2222)",
                    id="hostname",
                ),
                Input(
                    placeholder="Username",
                    id="username",
                ),
                Label(
                    "Use password if you are not using SSH key",
                    id="label_andor",
                ),
                Input(
                    placeholder="Password",
                    id="password",
                    password=True,
                ),
                Label(
                    "Crontab user (optional, for root/sudo access)",
                    id="label_crontab_user",
                ),
                Input(
                    placeholder="Leave empty for current user",
                    id="crontab_user",
                ),
                Horizontal(
                    Button("Add Server", variant="primary", id="add"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                ),
                id="content",
            ),
            id="dialog",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if self.query("#error"):
            label_error = self.query_one("#error")
            label_error.remove()

        error_labels = self.query("#error")
        for label in error_labels:
            label.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(False)
            return

        if event.button.id == "add":
            host_info = self.query_one("#hostname", Input).value.strip()
            username = self.query_one("#username", Input).value.strip()
            password = self.query_one("#password", Input).value.strip()
            content = self.query_one("#content", Vertical)
            crontab_user = self.query_one("#crontab_user", Input).value.strip()

            try:
                hostname, port = self._parse_host_info(host_info)
            except ValueError as exc:
                if not self.query("#error"):
                    message = str(exc) if str(exc) else "Invalid host format"
                    error_label = Label(message, id="error")
                    content.mount(error_label)
                return

            server = {
                "hostname": hostname,
                "port": port,
                "username": username,
                "password": password,
                "ssh_key": True if not password else False,
                "crontab_user": crontab_user if crontab_user else None,
            }

            self.dismiss(server)
