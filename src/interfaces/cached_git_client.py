"""Cached Git client implementation that wraps another Git client."""

from pathlib import Path
from typing import List, Optional, Union

from ..cache import CacheManager, get_cache_manager
from .git_client import GitClient, GitCommit, GitFileChange


class CachedGitClient(GitClient):
    """Git client wrapper that caches expensive operations."""

    def __init__(
        self, git_client: GitClient, cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize cached Git client.

        Args:
            git_client: The underlying Git client to wrap
            cache_manager: Optional cache manager (uses global if not provided)
        """
        self._git = git_client
        self._cache = cache_manager or get_cache_manager()

    def is_git_repo(self, path: Union[str, Path]) -> bool:
        """Check if path is a Git repository (not cached - fast operation)."""
        return self._git.is_git_repo(path)

    def get_current_branch(self, repo_path: Union[str, Path]) -> str:
        """Get current branch name (cached with short TTL)."""
        cache_params = {"repo_path": str(repo_path)}

        # Try cache first (with shorter TTL since branches can change)
        cached = self._cache.get("git_current_branch", cache_params)
        if cached is not None:
            return cached

        # Get from Git
        branch = self._git.get_current_branch(repo_path)

        # Cache with shorter TTL (60 seconds)
        self._cache.set("git_current_branch", cache_params, branch, ttl=60)

        return branch

    def get_changed_files(
        self,
        repo_path: Union[str, Path],
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        include_untracked: bool = True,
    ) -> List[GitFileChange]:
        """Get list of changed files (cached)."""
        cache_params = {
            "repo_path": str(repo_path),
            "base_ref": base_ref or "default",
            "head_ref": head_ref or "default",
            "include_untracked": include_untracked,
        }

        # Try cache first
        cached = self._cache.get("git_changed_files", cache_params)
        if cached is not None:
            # Reconstruct GitFileChange objects from cached data
            return [GitFileChange(**change_data) for change_data in cached]

        # Get from Git
        changes = self._git.get_changed_files(
            repo_path, base_ref, head_ref, include_untracked
        )

        # Cache as dictionaries
        cache_data = [
            {
                "file_path": change.file_path,
                "status": change.status,
                "additions": change.additions,
                "deletions": change.deletions,
                "old_path": change.old_path,
            }
            for change in changes
        ]
        self._cache.set("git_changed_files", cache_params, cache_data)

        return changes

    def get_file_diff(
        self,
        repo_path: Union[str, Path],
        file_path: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
    ) -> str:
        """Get diff for a specific file (cached)."""
        cache_params = {
            "repo_path": str(repo_path),
            "file_path": file_path,
            "base_ref": base_ref or "default",
            "head_ref": head_ref or "default",
        }

        # Try cache first
        cached = self._cache.get("git_file_diff", cache_params)
        if cached is not None:
            return cached

        # Get from Git
        diff = self._git.get_file_diff(repo_path, file_path, base_ref, head_ref)

        # Cache the result
        self._cache.set("git_file_diff", cache_params, diff)

        return diff

    def get_remote_url(
        self, repo_path: Union[str, Path], remote: str = "origin"
    ) -> Optional[str]:
        """Get remote URL (cached)."""
        cache_params = {"repo_path": str(repo_path), "remote": remote}

        # Try cache first
        cached = self._cache.get("git_remote_url", cache_params)
        if cached is not None:
            return cached if cached != "None" else None

        # Get from Git
        url = self._git.get_remote_url(repo_path, remote)

        # Cache the result (store "None" string for null values)
        self._cache.set(
            "git_remote_url", cache_params, url if url is not None else "None"
        )

        return url

    def get_repo_root(self, path: Union[str, Path]) -> Optional[Path]:
        """Get repository root directory (cached)."""
        cache_params = {"path": str(path)}

        # Try cache first
        cached = self._cache.get("git_repo_root", cache_params)
        if cached is not None:
            return Path(cached) if cached != "None" else None

        # Get from Git
        root = self._git.get_repo_root(path)

        # Cache the result
        self._cache.set("git_repo_root", cache_params, str(root) if root else "None")

        return root

    def get_commits(
        self, repo_path: Union[str, Path], branch: Optional[str] = None, limit: int = 10
    ) -> List[GitCommit]:
        """Get list of commits (cached)."""
        cache_params = {
            "repo_path": str(repo_path),
            "branch": branch or "current",
            "limit": limit,
        }

        # Try cache first
        cached = self._cache.get("git_commits", cache_params)
        if cached is not None:
            # Reconstruct GitCommit objects from cached data
            return [GitCommit(**commit_data) for commit_data in cached]

        # Get from Git
        commits = self._git.get_commits(repo_path, branch, limit)

        # Cache as dictionaries
        cache_data = [
            {
                "sha": commit.sha,
                "author": commit.author,
                "date": commit.date,
                "message": commit.message,
            }
            for commit in commits
        ]
        self._cache.set("git_commits", cache_params, cache_data)

        return commits

    def get_file_content(
        self, repo_path: Union[str, Path], file_path: str, ref: Optional[str] = None
    ) -> Optional[str]:
        """Get content of a file at a specific revision (cached)."""
        cache_params = {
            "repo_path": str(repo_path),
            "file_path": file_path,
            "ref": ref or "working_tree",
        }

        # Try cache first
        cached = self._cache.get("git_file_content", cache_params)
        if cached is not None:
            return cached if cached != "None" else None

        # Get from Git
        content = self._git.get_file_content(repo_path, file_path, ref)

        # Cache the result (store "None" string for null values)
        self._cache.set(
            "git_file_content", cache_params, content if content is not None else "None"
        )

        return content

    def invalidate_cache(
        self, operation: Optional[str] = None, repo_path: Optional[Path] = None
    ) -> int:
        """
        Invalidate Git caches.

        Args:
            operation: Specific operation to invalidate, or None for all
            repo_path: Specific repository to invalidate, or None for all

        Returns:
            Number of entries invalidated
        """
        if operation and repo_path:
            # Invalidate specific operation for specific repo
            return self._cache.invalidate(
                f"git_{operation}", {"repo_path": str(repo_path)}
            )
        elif operation:
            # Invalidate all entries for an operation
            return self._cache.invalidate(f"git_{operation}")
        else:
            # Invalidate all Git operations
            count = 0
            for op in [
                "current_branch",
                "changed_files",
                "file_diff",
                "remote_url",
                "repo_root",
                "commits",
                "file_content",
            ]:
                count += self._cache.invalidate(f"git_{op}")
            return count
