from textual.app import ComposeResult
from crontab import CronTab
from textual.binding import Binding

from cronboard.services.messages import CronJobDeleted
from textual.widgets import Button, Label
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen


class CronDeleteConfirmation(ModalScreen[bool]):
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
    ) -> None:
        super().__init__()
        self.server = server
        self.job = job
        self.cron = cron if cron else CronTab(user=True)
        self.remote = remote
        self.ssh_client = ssh_client
        self.message = message
        self.crontab_user = crontab_user

    def compose(self) -> ComposeResult:
        if self.message:
            display_message = self.message
        elif self.server:
            display_message = (
                f"Are you sure you want to delete the server '{self.server}' ?"
            )
        elif self.job:
            deletion = self.job.comment if self.job.comment else "this job"
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

    async def action_close_modal(self):
        await self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "delete":
            self.dismiss(False)
            return

        if self.job and self.cron:
            comment = getattr(self.job, "comment", None)
            ident = (
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
        self.dismiss(True)

    def write_remote_crontab(self):
        """Writes the current SSH cron table back to the remote server."""
        if not (self.remote and self.ssh_client):
            return False

        try:
            new_crontab_content = self.cron.render() or ""

            crontab_cmd = (
                f"crontab -u {self.crontab_user} -"
                if self.crontab_user
                else "crontab -"
            )
            stdin, _, stderr = self.ssh_client.exec_command(crontab_cmd)
            stdin.write(new_crontab_content)
            stdin.channel.shutdown_write()

            exit_status = stdin.channel.recv_exit_status()
            errors = stderr.read().decode().strip()

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
