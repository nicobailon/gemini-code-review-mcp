from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union


@dataclass(frozen=True)
class GitFileChange:
    """Represents a file change in Git."""

    file_path: str
    status: str  # Added, Modified, Deleted, Renamed
    additions: int = 0
    deletions: int = 0
    old_path: Optional[str] = None  # For renames


@dataclass(frozen=True)
class GitCommit:
    """Represents a Git commit."""

    sha: str
    author: str
    date: str
    message: str


class GitClient(ABC):
    """Abstract interface for Git operations."""

    @abstractmethod
    def is_git_repo(self, path: Union[str, Path]) -> bool:
        """Check if the given path is inside a Git repository."""
        pass

    @abstractmethod
    def get_repo_root(self, path: Union[str, Path]) -> Optional[Path]:
        """Get the root directory of the Git repository."""
        pass

    @abstractmethod
    def get_current_branch(self, repo_path: Union[str, Path]) -> str:
        """Get the name of the current branch."""
        pass

    @abstractmethod
    def get_changed_files(
        self,
        repo_path: Union[str, Path],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        include_untracked: bool = True,
    ) -> List[GitFileChange]:
        """
        Get list of changed files.

        Args:
            repo_path: Path to the repository
            base_ref: Base reference (commit/branch) to compare against
            head_ref: Head reference (commit/branch) to compare
            include_untracked: Whether to include untracked files

        Returns:
            List of GitFileChange objects
        """
        pass

    @abstractmethod
    def get_file_diff(
        self,
        repo_path: Union[str, Path],
        file_path: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> str:
        """
        Get diff for a specific file.

        Args:
            repo_path: Path to the repository
            file_path: Path to the file relative to repo root
            base_ref: Base reference to compare against
            head_ref: Head reference to compare

        Returns:
            Diff content as string
        """
        pass

    @abstractmethod
    def get_commits(
        self, repo_path: Union[str, Path], branch: Optional[str] = None, limit: int = 10
    ) -> List[GitCommit]:
        """
        Get list of commits.

        Args:
            repo_path: Path to the repository
            branch: Branch name (None for current branch)
            limit: Maximum number of commits to return

        Returns:
            List of GitCommit objects
        """
        pass

    @abstractmethod
    def get_remote_url(
        self, repo_path: Union[str, Path], remote: str = "origin"
    ) -> Optional[str]:
        """Get the URL of a remote repository."""
        pass

    @abstractmethod
    def get_file_content(
        self, repo_path: Union[str, Path], file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get content of a file at a specific revision.

        Args:
            repo_path: Path to the repository
            file_path: Path to the file relative to repo root
            ref: Git reference (commit/branch/tag), None for working tree

        Returns:
            File content or None if file doesn't exist
        """
        pass
