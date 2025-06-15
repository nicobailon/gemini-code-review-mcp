from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union


class FileSystem(ABC):
    """Abstract interface for file system operations."""

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if a file or directory exists."""
        pass

    @abstractmethod
    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if path is a file."""
        pass

    @abstractmethod
    def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if path is a directory."""
        pass

    @abstractmethod
    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        pass

    @abstractmethod
    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text content to a file."""
        pass

    @abstractmethod
    def list_dir(self, path: Union[str, Path]) -> List[Path]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def glob(self, path: Union[str, Path], pattern: str) -> List[Path]:
        """Find files matching a glob pattern."""
        pass

    @abstractmethod
    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ) -> None:
        """Create a directory."""
        pass

    @abstractmethod
    def remove(self, path: Union[str, Path]) -> None:
        """Remove a file."""
        pass

    @abstractmethod
    def rmdir(self, path: Union[str, Path]) -> None:
        """Remove a directory."""
        pass

    @abstractmethod
    def get_cwd(self) -> Path:
        """Get current working directory."""
        pass

    @abstractmethod
    def resolve(self, path: Union[str, Path]) -> Path:
        """Resolve a path to absolute form."""
        pass
