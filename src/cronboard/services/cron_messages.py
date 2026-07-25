from __future__ import annotations
from paramiko.client import SSHClient

from typing import Any

from textual.message import Message


class CronJobDeleted(Message):
    """Message posted when a cronjob is deleted.

    Attributes:
        identificator: The identificator of the cronjob.
        ssh_client: Paramiko SSH client for remote operations.
    """

    def __init__(
        self,
        identificator: str,
        *,
        ssh_client: Any = None,
    ) -> None:
        self.identificator: str = identificator
        self.ssh_client: SSHClient = ssh_client
        super().__init__()
