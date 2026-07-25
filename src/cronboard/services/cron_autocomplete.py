import os
from os import DirEntry
from pathlib import Path

from paramiko.client import SSHClient
from paramiko.sftp_client import SFTPClient
from textual.content import Content
from textual.widgets import Input
from textual_autocomplete import (
    DropdownItem,
    PathAutoComplete,
    TargetState,
)
from textual_autocomplete._path_autocomplete import (
    PathDropdownItem,
)

from cronboard.services.cron_dir_entry import CronDirEntry
from cronboard.services.cron_logging.cron_wrapper import get_files, get_remote_home


class CronAutoComplete(PathAutoComplete):
    """Textual widget for autocompleting cronjob commands.

    Attributes:
        ssh_client: SSH client for remote operations.
        target_state: Target state of the input.
        directory_cache: Directory cache for caching directory entries.
    """

    def __init__(self, target, ssh_client=None):
        super().__init__(target)
        self.ssh_client: SSHClient | None = ssh_client
        self.target_state: TargetState = target
        self.directory_cache: dict[str, list[CronDirEntry]] = {}
        self._dropdown_results_cache: dict[str, list[DropdownItem]] = {}
        self._sftp: SFTPClient | None = None
        self._remote_home: str | None = None

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        """Get the candidates for the current path segment. This is called each time the input changes or the cursor position changes.

        Args:
            target_state: Target state of the input.

        Returns:
            A list of DropdownItem objects with the candidates for the current path segment.

        """

        if self.ssh_client:
            if not self._remote_home:
                self._remote_home: str | None = get_remote_home(self.ssh_client)
            if self._remote_home:
                home_path = Path(self._remote_home)
        else:
            home_path: Path = Path.home()

        current_input_full: str = target_state.text[: target_state.cursor_position]
        # Hide Autocomplete when entering new command section
        if current_input_full.endswith(" "):
            return []
        # Get the last segment of the current full input
        current_input: str = (
            current_input_full.split()[-1] if current_input_full else ""
        )

        if "/" in current_input:
            last_slash_index: int = current_input.rindex("/")
            path_segment: str = current_input[:last_slash_index] or "/"
            directory: Path = (
                home_path / path_segment if path_segment != "/" else self.path
            )
        else:
            directory: Path = home_path

        # Use the directory path as the cache key
        cache_key = str(directory)
        cached_entries: list[CronDirEntry] | None = self.directory_cache.get(cache_key)

        if cached_entries is not None:
            entries: list[CronDirEntry] = cached_entries
        else:
            try:
                if not self.ssh_client:
                    objects: list[DirEntry[str]] = list(os.scandir(directory))
                    entries: list[CronDirEntry] = []

                    for object in objects:
                        cron_dir_entry = CronDirEntry(
                            object.name, object.path, object.is_dir()
                        )
                        entries.append(cron_dir_entry)
                else:
                    if not self._sftp:
                        self._sftp: SFTPClient = self.ssh_client.open_sftp()

                    entries: list[CronDirEntry] = get_files(
                        self.ssh_client, str(directory), sftp=self._sftp
                    )

                self.directory_cache[cache_key] = entries
            except OSError:
                return []

        cached_results: list[DropdownItem] | None = self._dropdown_results_cache.get(
            cache_key
        )

        if cached_results:
            return cached_results

        results: list[tuple[PathDropdownItem, bool]] = []
        for entry in entries:
            completion: str = entry.name
            if not self.show_dotfiles and completion.startswith("."):
                continue
            if entry.is_dir():
                completion += "/"
            results.append(
                (PathDropdownItem(completion, path=Path(entry.path)), entry.is_dir())
            )

        results.sort(key=lambda x: self.sort_key(x[0]))
        folder_prefix: Content = self.folder_prefix
        file_prefix: Content = self.file_prefix
        dropdown_items: list[DropdownItem] = [
            DropdownItem(
                item.main,
                prefix=folder_prefix if is_dir else file_prefix,
            )
            for item, is_dir in results
        ]
        self._dropdown_results_cache[cache_key] = dropdown_items
        return dropdown_items

    def on_unmount(self) -> None:
        """Close the SFTP connection on unmount."""

        if self._sftp:
            self._sftp.close()
            self._sftp = None

    def get_search_string(self, target_state: TargetState) -> str:
        """Return only the current path segment for searching in the dropdown.

        Args:
            target_state: The target state of the input.

        Returns:
            The current path segment.

        """

        current_input_full: str = target_state.text[
            : target_state.cursor_position
        ].strip()
        # Get the last segment of the current full input
        current_input: str = (
            current_input_full.split()[-1] if current_input_full else ""
        )

        if "/" in current_input:
            last_slash_index: int = current_input.rindex("/")
            search_string: str = current_input[last_slash_index + 1 :]
            return search_string
        else:
            return current_input

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Apply the completion by replacing only the current path segment.

        Args:
            value: The value to apply.
            state: The target state of the input.
        """

        def get_new_path_string(path_input: str, cursor_position: int):
            # There's a slash before the cursor, so we only want to replace
            # the text after the last slash with the selected value
            try:
                replace_start_index: int = path_input.rindex("/", 0, cursor_position)
            except ValueError:
                # No slashes, so we do a full replacement
                new_value: str = value
                new_cursor_position: int = len(value)
            else:
                # Keep everything before and including the slash before the cursor.
                path_prefix: str = path_input[: replace_start_index + 1]
                new_value: str = path_prefix + value
                new_cursor_position: int = len(path_prefix) + len(value)
            return new_value, new_cursor_position

        target: Input = self.target
        current_input: str = state.text.strip()
        cursor_position: int = state.cursor_position

        # Get relevant space separated segment to complete, to keep other segments intact
        # e.g. "cp PATH_1 PATH_2" we must check which part to complete and keep the rest of the string

        string_before = ""
        string_after = ""
        # Exactly two parts to complete
        if len(current_input.split()) == 2:
            first_split_index: int = current_input.index(" ")
            # completing the first part
            if cursor_position <= first_split_index + 1:
                string_to_replace: str = current_input[:first_split_index]
                string_after: str = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
            # completing the second part
            else:
                string_before: str = current_input[:first_split_index]
                string_to_replace: str = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
                new_cursor_position += len(string_before) + 1

        # More than two parts
        elif len(current_input.split()) > 2:
            if current_input.index(" ") >= cursor_position:
                first_split_index: int = current_input.index(" ")
            else:
                first_split_index: int = current_input.rindex(" ", 0, cursor_position)

            if current_input.rindex(" ") <= cursor_position:
                last_split_index: int = current_input.rindex(" ")
            else:
                last_split_index: int = current_input.index(" ", cursor_position)
            # completing the first part
            if cursor_position <= first_split_index + 1:
                string_to_replace: str = current_input[:first_split_index]
                string_after: str = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
            # completing the last part
            elif first_split_index + 1 < cursor_position < last_split_index + 1:
                string_before: str = current_input[:first_split_index]
                string_to_replace: str = current_input[
                    first_split_index + 1 : last_split_index
                ]
                string_after: str = current_input[last_split_index:]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
                new_cursor_position += len(string_before) + 1
            # completing the last part
            else:
                string_before: str = current_input[:first_split_index]
                string_to_replace: str = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
                new_cursor_position += len(string_before) + 1
        # Only one part to complete
        else:
            new_value, new_cursor_position = get_new_path_string(
                path_input=current_input, cursor_position=cursor_position
            )

        with self.prevent(Input.Changed):
            target.value = " ".join(
                [
                    part.strip()
                    for part in [string_before, new_value, string_after]
                    if part
                ]
            )
            target.cursor_position = new_cursor_position

    def post_completion(self) -> None:
        """Hide the autocomplete if the input is not a directory."""

        if not self.target.value.endswith("/"):
            self.action_hide()
