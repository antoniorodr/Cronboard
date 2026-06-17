from textual_autocomplete import (
    DropdownItem,
    PathAutoComplete,
    TargetState,
)
from textual_autocomplete._path_autocomplete import (
    PathDropdownItem,
)
import os
from pathlib import Path
from textual.widgets import Input


class CronAutoComplete(PathAutoComplete):
    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        """Get the candidates for the current path segment.

        This is called each time the input changes or the cursor position changes/
        """
        home_path = Path.home()
        current_input_full = target_state.text[: target_state.cursor_position]
        # Hide Autocomplete when entering new command section
        if current_input_full.endswith(" "):
            return []
        # Get the last segment of the current full input
        current_input = current_input_full.split()[-1] if current_input_full else ""

        if "/" in current_input:
            last_slash_index = current_input.rindex("/")
            path_segment = current_input[:last_slash_index] or "/"
            directory = home_path / path_segment if path_segment != "/" else self.path
        else:
            directory = home_path

        # Use the directory path as the cache key
        cache_key = str(directory)
        cached_entries = self._directory_cache.get(cache_key)

        if cached_entries is not None:
            entries = cached_entries
        else:
            try:
                entries = list(os.scandir(directory))
                self._directory_cache[cache_key] = entries
            except OSError:
                return []

        results: list[PathDropdownItem] = []
        for entry in entries:
            # Only include the entry name, not the full path
            completion = entry.name
            if not self.show_dotfiles and completion.startswith("."):
                continue
            if entry.is_dir():
                completion += "/"
            results.append(PathDropdownItem(completion, path=Path(entry.path)))

        results.sort(key=self.sort_key)
        folder_prefix = self.folder_prefix
        file_prefix = self.file_prefix
        return [
            DropdownItem(
                item.main,
                prefix=folder_prefix if item.path.is_dir() else file_prefix,
            )
            for item in results
        ]

    def get_search_string(self, target_state: TargetState) -> str:
        """Return only the current path segment for searching in the dropdown."""
        current_input_full = target_state.text[: target_state.cursor_position].strip()
        # Get the last segment of the current full input
        current_input = current_input_full.split()[-1] if current_input_full else ""

        if "/" in current_input:
            last_slash_index = current_input.rindex("/")
            search_string = current_input[last_slash_index + 1 :]
            return search_string
        else:
            return current_input

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Apply the completion by replacing only the current path segment."""

        def get_new_path_string(path_input: str, cursor_position: int):
            # There's a slash before the cursor, so we only want to replace
            # the text after the last slash with the selected value
            try:
                replace_start_index = path_input.rindex("/", 0, cursor_position)
            except ValueError:
                # No slashes, so we do a full replacement
                new_value = value
                new_cursor_position = len(value)
            else:
                # Keep everything before and including the slash before the cursor.
                path_prefix = path_input[: replace_start_index + 1]
                new_value = path_prefix + value
                new_cursor_position = len(path_prefix) + len(value)
            return new_value, new_cursor_position

        target = self.target
        current_input = state.text.strip()
        cursor_position = state.cursor_position

        # Get relevant space separated segment to complete, to keep other segments intact
        # e.g. "cp PATH_1 PATH_2" we must check which part to complete and keep the rest of the string

        string_before = ""
        string_after = ""
        # Exactly two parts to complete
        if len(current_input.split()) == 2:
            first_split_index = current_input.index(" ")
            # completing the first part
            if cursor_position <= first_split_index + 1:
                string_to_replace = current_input[:first_split_index]
                string_after = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
            # completing the second part
            else:
                string_before = current_input[:first_split_index]
                string_to_replace = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
                new_cursor_position += len(string_before) + 1

        # More than two parts
        elif len(current_input.split()) > 2:
            if current_input.index(" ") >= cursor_position:
                first_split_index = current_input.index(" ")
            else:
                first_split_index = current_input.rindex(" ", 0, cursor_position)

            if current_input.rindex(" ") <= cursor_position:
                last_split_index = current_input.rindex(" ")
            else:
                last_split_index = current_input.index(" ", cursor_position)
            # completing the first part
            if cursor_position <= first_split_index + 1:
                string_to_replace = current_input[:first_split_index]
                string_after = current_input[first_split_index + 1 :]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
            # completing the last part
            elif first_split_index + 1 < cursor_position < last_split_index + 1:
                string_before = current_input[:first_split_index]
                string_to_replace = current_input[
                    first_split_index + 1 : last_split_index
                ]
                string_after = current_input[last_split_index:]
                new_value, new_cursor_position = get_new_path_string(
                    path_input=string_to_replace, cursor_position=cursor_position
                )
                new_cursor_position += len(string_before) + 1
            # completing the last part
            else:
                string_before = current_input[:first_split_index]
                string_to_replace = current_input[first_split_index + 1 :]
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
        if not self.target.value.endswith("/"):
            self.action_hide()
