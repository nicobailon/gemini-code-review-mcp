"""Cached filesystem implementation that wraps another filesystem."""

from pathlib import Path
from typing import List, Optional, Union

from ..cache import CacheManager, get_cache_manager
from .filesystem import FileSystem


class CachedFileSystem(FileSystem):
    """Filesystem wrapper that caches expensive operations."""

    def __init__(
        self, filesystem: FileSystem, cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize cached filesystem.

        Args:
            filesystem: The underlying filesystem to wrap
            cache_manager: Optional cache manager (uses global if not provided)
        """
        self._fs = filesystem
        self._cache = cache_manager or get_cache_manager()

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if a file or directory exists (not cached - fast operation)."""
        return self._fs.exists(path)

    def is_file(self, path: Union[str, Path]) -> bool:
        """Check if path is a file (not cached - fast operation)."""
        return self._fs.is_file(path)

    def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if path is a directory (not cached - fast operation)."""
        return self._fs.is_dir(path)

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text content from a file (cached for repeated reads)."""
        cache_params = {"path": str(path), "encoding": encoding}

        # Try cache first
        cached = self._cache.get("fs_read_text", cache_params)
        if cached is not None:
            return cached

        # Read from filesystem
        content = self._fs.read_text(path, encoding)

        # Cache the result
        self._cache.set("fs_read_text", cache_params, content)

        return content

    def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text content to a file (invalidates cache)."""
        # Invalidate cache for this file
        cache_params = {"path": str(path), "encoding": encoding}
        self._cache.invalidate("fs_read_text", cache_params)

        # Write to filesystem
        self._fs.write_text(path, content, encoding)

    def list_dir(self, path: Union[str, Path]) -> List[Path]:
        """List contents of a directory (cached)."""
        cache_params = {"path": str(path)}

        # Try cache first
        cached = self._cache.get("fs_list_dir", cache_params)
        if cached is not None:
            # Convert strings back to Path objects
            return [Path(p) for p in cached]

        # List from filesystem
        contents = self._fs.list_dir(path)

        # Cache as strings (Path objects aren't JSON serializable)
        self._cache.set("fs_list_dir", cache_params, [str(p) for p in contents])

        return contents

    def glob(self, path: Union[str, Path], pattern: str) -> List[Path]:
        """Find files matching a glob pattern (cached)."""
        cache_params = {"path": str(path), "pattern": pattern}

        # Try cache first
        cached = self._cache.get("fs_glob", cache_params)
        if cached is not None:
            return [Path(p) for p in cached]

        # Glob from filesystem
        matches = self._fs.glob(path, pattern)

        # Cache as strings
        self._cache.set("fs_glob", cache_params, [str(p) for p in matches])

        return matches

    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ) -> None:
        """Create a directory (invalidates directory listing cache)."""
        # Invalidate parent directory listing
        parent = Path(path).parent
        self._cache.invalidate("fs_list_dir", {"path": str(parent)})

        # Create directory
        self._fs.mkdir(path, parents, exist_ok)

    def remove(self, path: Union[str, Path]) -> None:
        """Remove a file (invalidates caches)."""
        # Invalidate file content cache
        self._cache.invalidate("fs_read_text", {"path": str(path), "encoding": "utf-8"})

        # Invalidate parent directory listing
        parent = Path(path).parent
        self._cache.invalidate("fs_list_dir", {"path": str(parent)})

        # Remove file
        self._fs.remove(path)

    def rmdir(self, path: Union[str, Path]) -> None:
        """Remove a directory (invalidates caches)."""
        # Invalidate directory listing for this dir
        self._cache.invalidate("fs_list_dir", {"path": str(path)})

        # Invalidate parent directory listing
        parent = Path(path).parent
        self._cache.invalidate("fs_list_dir", {"path": str(parent)})

        # Remove directory
        self._fs.rmdir(path)

    def get_cwd(self) -> Path:
        """Get current working directory (not cached - can change)."""
        return self._fs.get_cwd()

    def resolve(self, path: Union[str, Path]) -> Path:
        """Resolve a path to absolute form (not cached - fast operation)."""
        return self._fs.resolve(path)

    def invalidate_cache(self, operation: Optional[str] = None) -> int:
        """
        Invalidate filesystem caches.

        Args:
            operation: Specific operation to invalidate, or None for all

        Returns:
            Number of entries invalidated
        """
        if operation:
            return self._cache.invalidate(f"fs_{operation}")
        else:
            # Invalidate all filesystem operations
            count = 0
            for op in ["read_text", "list_dir", "glob"]:
                count += self._cache.invalidate(f"fs_{op}")
            return count
