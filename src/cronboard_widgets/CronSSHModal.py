from textual.app import ComposeResult
from textual.widgets import Button, Label, Input
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual import events


class CronSSHModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Vertical(
                Label(
                    "Add a remote server into the tree view",
                    id="label1",
                ),
                Input(
                    placeholder="Hostname (e.g. localhost:2222)",
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
                Horizontal(
                    Button("Add Server", variant="primary", id="add"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                ),
                id="content",
            ),
            id="dialog",
        )

    def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.save_content()
        elif event.key == "escape":
            self.dismiss(False)

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
        elif event.button.id == "add":
            self.save_content()

    def save_content(self) -> None:
        host_info = self.query_one("#hostname", Input).value.strip()
        username = self.query_one("#username", Input).value.strip()
        password = self.query_one("#password", Input).value.strip()
        content = self.query_one("#content", Vertical)

        try:
            hostname, port = host_info.split(":")
            port = int(port)
        except ValueError:
            if not self.query("#error"):
                error_label = Label(
                    "Invalid host format. Use host:port", id="error"
                )
                content.mount(error_label)

        server = {
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": password,
            "ssh_key": True if not password else False,
        }

        self.dismiss(server)
