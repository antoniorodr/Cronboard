class CronDirEntry:
    """Represents a directory entry, mirroring the os.DirEntry object.

    Attributes:
        name: The name of the directory entry.
        path: The path of the directory entry.
        is_dir: Whether the directory entry is a directory.
    """

    def __init__(self, name: str, path: str, is_dir: bool):
        self.name: str = name
        self.path: str = path
        self._is_dir: bool = is_dir

    def is_dir(self):
        """Returns whether the directory entry is a directory.

        Returns:
            True if the directory entry is a directory, else False.
        """

        return self._is_dir
