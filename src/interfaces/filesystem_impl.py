from pathlib import Path
from typing import Dict, List, Union

from .filesystem import FileSystem


class ProductionFileSystem(FileSystem):
    """Production implementation of FileSystem using actual file system."""

    def exists(self, path: Union[str, Path]) -> bool:
        return Path(path).exists()

    def is_file(self, path: Union[str, Path]) -> bool:
        return Path(path).is_file()

    def is_dir(self, path: Union[str, Path]) -> bool:
        return Path(path).is_dir()

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        return Path(path).read_text(encoding=encoding)

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        Path(path).write_text(content, encoding=encoding)

    def list_dir(self, path: Union[str, Path]) -> List[Path]:
        return list(Path(path).iterdir())

    def glob(self, path: Union[str, Path], pattern: str) -> List[Path]:
        return list(Path(path).glob(pattern))

    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ) -> None:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def remove(self, path: Union[str, Path]) -> None:
        Path(path).unlink()

    def rmdir(self, path: Union[str, Path]) -> None:
        Path(path).rmdir()

    def get_cwd(self) -> Path:
        return Path.cwd()

    def resolve(self, path: Union[str, Path]) -> Path:
        return Path(path).resolve()


class InMemoryFileSystem(FileSystem):
    """In-memory implementation of FileSystem for testing."""

    def __init__(self):
        self._files: Dict[str, str] = {}
        self._dirs: set[str] = {"/"}
        self._cwd = Path("/")

    def _normalize_path(self, path: Union[str, Path]) -> str:
        """Normalize path to absolute string format."""
        p = Path(path)
        if not p.is_absolute():
            p = self._cwd / p
        return str(p.resolve())

    def exists(self, path: Union[str, Path]) -> bool:
        norm_path = self._normalize_path(path)
        return norm_path in self._files or norm_path in self._dirs

    def is_file(self, path: Union[str, Path]) -> bool:
        return self._normalize_path(path) in self._files

    def is_dir(self, path: Union[str, Path]) -> bool:
        return self._normalize_path(path) in self._dirs

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        norm_path = self._normalize_path(path)
        if norm_path not in self._files:
            raise FileNotFoundError(f"No such file: {path}")
        return self._files[norm_path]

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        norm_path = self._normalize_path(path)
        parent = str(Path(norm_path).parent)
        if parent not in self._dirs:
            raise FileNotFoundError(f"Parent directory does not exist: {parent}")
        self._files[norm_path] = content

    def list_dir(self, path: Union[str, Path]) -> List[Path]:
        norm_path = self._normalize_path(path)
        if norm_path not in self._dirs:
            raise FileNotFoundError(f"No such directory: {path}")

        results: List[Path] = []
        norm_path_with_slash = norm_path.rstrip("/") + "/"

        # Find all direct children
        for file_path in self._files:
            if file_path.startswith(norm_path_with_slash):
                relative = file_path[len(norm_path_with_slash) :]
                if "/" not in relative:  # Direct child
                    results.append(Path(file_path))

        for dir_path in self._dirs:
            if dir_path != norm_path and dir_path.startswith(norm_path_with_slash):
                relative = dir_path[len(norm_path_with_slash) :]
                if "/" not in relative.rstrip("/"):  # Direct child
                    results.append(Path(dir_path))

        return results

    def glob(self, path: Union[str, Path], pattern: str) -> List[Path]:
        """Simple glob implementation for testing."""
        norm_path = self._normalize_path(path)
        results: List[Path] = []

        # Convert glob pattern to simple matching
        import fnmatch

        full_pattern = str(Path(norm_path) / pattern)

        for file_path in self._files:
            if fnmatch.fnmatch(file_path, full_pattern):
                results.append(Path(file_path))

        for dir_path in self._dirs:
            if fnmatch.fnmatch(dir_path, full_pattern):
                results.append(Path(dir_path))

        return results

    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ) -> None:
        norm_path = self._normalize_path(path)

        if norm_path in self._dirs:
            if not exist_ok:
                raise FileExistsError(f"Directory already exists: {path}")
            return

        if norm_path in self._files:
            raise FileExistsError(f"File already exists: {path}")

        parent = str(Path(norm_path).parent)
        if parent not in self._dirs:
            if parents:
                self.mkdir(parent, parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"Parent directory does not exist: {parent}")

        self._dirs.add(norm_path)

    def remove(self, path: Union[str, Path]) -> None:
        norm_path = self._normalize_path(path)
        if norm_path not in self._files:
            raise FileNotFoundError(f"No such file: {path}")
        del self._files[norm_path]

    def rmdir(self, path: Union[str, Path]) -> None:
        norm_path = self._normalize_path(path)
        if norm_path not in self._dirs:
            raise FileNotFoundError(f"No such directory: {path}")
        if norm_path == "/":
            raise PermissionError("Cannot remove root directory")

        # Check if directory is empty
        norm_path_with_slash = norm_path.rstrip("/") + "/"
        for file_path in self._files:
            if file_path.startswith(norm_path_with_slash):
                raise OSError(f"Directory not empty: {path}")

        for dir_path in self._dirs:
            if dir_path != norm_path and dir_path.startswith(norm_path_with_slash):
                raise OSError(f"Directory not empty: {path}")

        self._dirs.remove(norm_path)

    def get_cwd(self) -> Path:
        return self._cwd

    def resolve(self, path: Union[str, Path]) -> Path:
        return Path(self._normalize_path(path))
