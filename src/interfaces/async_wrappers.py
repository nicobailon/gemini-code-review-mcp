"""Async wrappers for filesystem and Git operations using asyncio.to_thread()."""

import asyncio
from pathlib import Path
from typing import List, Optional, Union

from .filesystem import FileSystem
from .git_client import GitClient, GitFileChange


class AsyncFileSystemWrapper:
    """Async wrapper for FileSystem operations using asyncio.to_thread()."""

    def __init__(self, filesystem: FileSystem):
        """Initialize with a filesystem implementation."""
        self._fs = filesystem

    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if a file or directory exists."""
        return await asyncio.to_thread(self._fs.exists, path)

    async def is_file(self, path: Union[str, Path]) -> bool:
        """Check if path is a file."""
        return await asyncio.to_thread(self._fs.is_file, path)

    async def is_dir(self, path: Union[str, Path]) -> bool:
        """Check if path is a directory."""
        return await asyncio.to_thread(self._fs.is_dir, path)

    async def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        return await asyncio.to_thread(self._fs.read_text, path, encoding)

    async def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> None:
        """Write text content to a file."""
        await asyncio.to_thread(self._fs.write_text, path, content, encoding)

    async def list_dir(self, path: Union[str, Path]) -> List[Path]:
        """List contents of a directory."""
        return await asyncio.to_thread(self._fs.list_dir, path)

    async def glob(self, path: Union[str, Path], pattern: str) -> List[Path]:
        """Find files matching a glob pattern."""
        return await asyncio.to_thread(self._fs.glob, path, pattern)

    async def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ) -> None:
        """Create a directory."""
        await asyncio.to_thread(self._fs.mkdir, path, parents, exist_ok)

    async def remove(self, path: Union[str, Path]) -> None:
        """Remove a file."""
        await asyncio.to_thread(self._fs.remove, path)

    async def rmdir(self, path: Union[str, Path]) -> None:
        """Remove a directory."""
        await asyncio.to_thread(self._fs.rmdir, path)

    async def get_cwd(self) -> Path:
        """Get current working directory."""
        return await asyncio.to_thread(self._fs.get_cwd)

    async def resolve(self, path: Union[str, Path]) -> Path:
        """Resolve a path to absolute form."""
        return await asyncio.to_thread(self._fs.resolve, path)


class AsyncGitClientWrapper:
    """Async wrapper for GitClient operations using asyncio.to_thread()."""

    def __init__(self, git_client: GitClient):
        """Initialize with a Git client implementation."""
        self._git = git_client

    async def is_git_repo(self, path: Path) -> bool:
        """Check if path is a Git repository."""
        return await asyncio.to_thread(self._git.is_git_repo, path)

    async def get_current_branch(self, repo_path: Path) -> str:
        """Get current branch name."""
        return await asyncio.to_thread(self._git.get_current_branch, repo_path)

    async def get_changed_files(
        self, repo_path: Path, base_branch: Optional[str] = None
    ) -> List[GitFileChange]:
        """Get list of changed files."""
        return await asyncio.to_thread(
            self._git.get_changed_files, repo_path, base_branch
        )

    async def get_file_diff(
        self, repo_path: Path, file_path: str, base_branch: Optional[str] = None
    ) -> str:
        """Get diff for a specific file."""
        return await asyncio.to_thread(
            self._git.get_file_diff, repo_path, file_path, base_branch
        )

    # Note: get_commit_hash method removed as it doesn't exist in GitClient interface

    async def get_remote_url(
        self, repo_path: Path, remote: str = "origin"
    ) -> Optional[str]:
        """Get remote URL."""
        return await asyncio.to_thread(self._git.get_remote_url, repo_path, remote)

    async def get_repo_root(self, path: Path) -> Optional[Path]:
        """Get repository root directory."""
        return await asyncio.to_thread(self._git.get_repo_root, path)

    async def get_commits(
        self, repo_path: Path, branch: Optional[str] = None, limit: int = 10
    ):
        """Get list of commits."""
        return await asyncio.to_thread(self._git.get_commits, repo_path, branch, limit)

    async def get_file_content(
        self, repo_path: Path, file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        """Get content of a file at a specific revision."""
        return await asyncio.to_thread(
            self._git.get_file_content, repo_path, file_path, ref
        )


def create_async_filesystem(filesystem: FileSystem) -> AsyncFileSystemWrapper:
    """Create an async wrapper for a filesystem implementation."""
    return AsyncFileSystemWrapper(filesystem)


def create_async_git_client(git_client: GitClient) -> AsyncGitClientWrapper:
    """Create an async wrapper for a Git client implementation."""
    return AsyncGitClientWrapper(git_client)
