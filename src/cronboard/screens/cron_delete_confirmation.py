import tomlkit
from crontab import CronTab
from paramiko.client import SSHClient
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from cronboard.config import CRONBOARD_NOTIFICATIONS_FILE
from cronboard.services.cron_logging.cron_wrapper import (
    CONFIG_REL_PATH,
    _generate_notifications_config_for_server,
    get_remote_home,
)
from cronboard.services.cron_messages import CronJobDeleted


class CronDeleteConfirmation(ModalScreen[bool]):
    """Confirmation modal for deleting a cron job or server.

        Displays a contextual message based on what is being deleted
        (job or server). On confirmation, removes the
        job/server from the crontab, writes changes (local or remote), and
        posts a CronJobDeleted message. Returns True on delete, False on
    cancel.

        Args:
            job: Cronjob to delete.
            cron: CronTab instance to modify. Defaults to user's crontab.
            remote: Whether this is a remote crontab via SSH.
            ssh_client: Paramiko SSH client for remote operations.
            server: Server name.
            message: Confirmation message.
            crontab_user: CronTab instance for remote user-specific crontabs.
    """

    BINDINGS = [Binding(key="escape", action="close_modal", description="Close")]

    def __init__(
        self,
        job=None,
        cron=None,
        remote=False,
        ssh_client=None,
        server=None,
        message=None,
        crontab_user=None,
        server_name="local",
    ) -> None:
        super().__init__()
        self.server = server
        self.job = job
        self.cron: CronTab | None = cron if cron else CronTab(user=True)
        self.remote: bool = remote
        self.ssh_client: SSHClient | None = ssh_client
        self.message: str | None = message
        self.crontab_user: CronTab | None = crontab_user
        self.server_name: str = server_name

    def compose(self) -> ComposeResult:
        """Builds the modal UI: message to display and two buttons (Delete and Cancel)"""

        if self.message:
            display_message: str | None = self.message
        elif self.server:
            display_message = (
                f"Are you sure you want to delete the server '{self.server}' ?"
            )
        elif self.job:
            deletion: str | None = self.job.comment if self.job.comment else "this job"
            display_message = f"Are you sure you want to delete '{deletion}' ?"
        else:
            display_message = "Are you sure you want to proceed with deletion?"

        yield Grid(
            Vertical(
                Label(display_message, id="label1", classes="message"),
                Horizontal(
                    Button("Delete", variant="primary", id="delete"),
                    Button("Cancel", variant="error", id="cancel"),
                    id="button-row",
                ),
                id="content",
            ),
            id="dialog",
        )

    async def action_close_modal(self) -> None:
        await self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Decides the action depending on the button the user clicks. If "delete", it
        will delete the chosen object.

        Args:
            event: Button.Pressed object. Identifies the button throught id.
        """

        if event.button.id != "delete":
            self.dismiss(False)
            return

        if self.job and self.cron:
            comment: str | None = getattr(self.job, "comment", None)
            ident: str | None = (
                comment.strip()
                if isinstance(comment, str) and comment.strip()
                else None
            )

            self.cron.remove(self.job)

            if self.remote and self.ssh_client:
                self.write_remote_crontab()
            else:
                self.cron.write()

            if ident and self.is_mounted:
                self.app.post_message(
                    CronJobDeleted(
                        ident,
                        ssh_client=self.ssh_client if self.remote else None,
                    )
                )

            if ident:
                self.delete_notification(ident)

            if self.remote and self.ssh_client:
                self.push_notifications_to_remote()

        self.dismiss(True)

    def delete_notification(self, ident: str) -> None:
        """Deletes the notification entry for the cronjob in the notifications file."""

        try:
            with open(CRONBOARD_NOTIFICATIONS_FILE, "r") as f:
                config = tomlkit.loads(f.read())
        except FileNotFoundError:
            return

        server_section = config.get(self.server_name)
        if isinstance(server_section, dict) and ident in server_section:
            del server_section[ident]
            with open(CRONBOARD_NOTIFICATIONS_FILE, "w") as f:
                f.write(tomlkit.dumps(config))

    def push_notifications_to_remote(self) -> None:
        """Pushes the flattened notifications.toml to the remote server."""

        try:
            content = _generate_notifications_config_for_server(self.server_name)
            if content is None:
                return

            if self.ssh_client:
                home = get_remote_home(self.ssh_client)

            if not home:
                return

            remote_path = f"{home}/{CONFIG_REL_PATH}/notifications.toml"
            sftp = self.ssh_client.open_sftp()
            with sftp.open(remote_path, "w") as f:
                f.write(content)
            sftp.close()
        except Exception as e:
            print(f"Warning: Failed to sync notifications.toml to remote: {e}  ")

    def write_remote_crontab(self) -> bool:
        """Writes the current SSH cron table back to the remote server.

        Returns:
            True if success. Else False.

        """

        if not (self.remote and self.ssh_client):
            return False

        try:
            if self.cron:
                new_crontab_content: str = self.cron.render() or ""

            crontab_cmd: str = (
                f"crontab -u {self.crontab_user} -"
                if self.crontab_user
                else "crontab -"
            )
            stdin, _, stderr = self.ssh_client.exec_command(crontab_cmd)
            stdin.write(new_crontab_content)
            stdin.channel.shutdown_write()

            exit_status: str = stdin.channel.recv_exit_status()
            errors: str = stderr.read().decode().strip()

            if errors:
                print(f"❌ Failed to write remote crontab: {errors}")
                return False

            if exit_status != 0:
                print(f"❌ Command failed with exit status: {exit_status}")
                return False

            print("✅ Remote crontab updated successfully")
            return True

        except Exception as e:
            print(f"❌ Error writing remote crontab: {e}")
            return False
