"""
Dependency injection container for the application.

This module provides a simple manual DI container that manages
the creation and lifecycle of dependencies.
"""

from dataclasses import dataclass
from typing import Optional

try:
    from .cache import CacheManager, get_cache_manager
    from .interfaces import (
        AsyncFileSystemWrapper,
        AsyncGitClientWrapper,
        CachedFileSystem,
        CachedGitClient,
        FileSystem,
        GitClient,
        InMemoryFileSystem,
        InMemoryGitClient,
        ProductionFileSystem,
        ProductionGitClient,
        create_async_filesystem,
        create_async_git_client,
    )
    from .services import FileFinder
except ImportError:
    from cache import CacheManager, get_cache_manager
    from interfaces import (
        AsyncFileSystemWrapper,
        AsyncGitClientWrapper,
        CachedFileSystem,
        CachedGitClient,
        FileSystem,
        GitClient,
        InMemoryFileSystem,
        InMemoryGitClient,
        ProductionFileSystem,
        ProductionGitClient,
        create_async_filesystem,
        create_async_git_client,
    )
    from services import FileFinder


@dataclass
class Dependencies:
    """Container for application dependencies."""

    filesystem: FileSystem
    git_client: GitClient
    file_finder: FileFinder
    async_filesystem: Optional[AsyncFileSystemWrapper] = None
    async_git_client: Optional[AsyncGitClientWrapper] = None


class DependencyContainer:
    """Simple dependency injection container."""

    def __init__(self, use_production: bool = True, enable_cache: bool = True):
        """
        Initialize the container.

        Args:
            use_production: If True, use production implementations.
                           If False, use in-memory implementations for testing.
            enable_cache: If True, wrap production implementations with caching.
        """
        self.use_production = use_production
        self.enable_cache = enable_cache and use_production  # Only cache in production
        self._filesystem: Optional[FileSystem] = None
        self._git_client: Optional[GitClient] = None
        self._file_finder: Optional[FileFinder] = None
        self._cache_manager: Optional[CacheManager] = None
        self._async_filesystem: Optional[AsyncFileSystemWrapper] = None
        self._async_git_client: Optional[AsyncGitClientWrapper] = None

    @property
    def cache_manager(self) -> Optional[CacheManager]:
        """Get or create cache manager."""
        if self.enable_cache and self._cache_manager is None:
            self._cache_manager = get_cache_manager()
        return self._cache_manager

    @property
    def filesystem(self) -> FileSystem:
        """Get or create filesystem implementation."""
        if self._filesystem is None:
            if self.use_production:
                base_fs = ProductionFileSystem()
                if self.enable_cache:
                    self._filesystem = CachedFileSystem(base_fs, self.cache_manager)
                else:
                    self._filesystem = base_fs
            else:
                self._filesystem = InMemoryFileSystem()
        return self._filesystem

    @property
    def git_client(self) -> GitClient:
        """Get or create git client implementation."""
        if self._git_client is None:
            if self.use_production:
                base_git = ProductionGitClient()
                if self.enable_cache:
                    self._git_client = CachedGitClient(base_git, self.cache_manager)
                else:
                    self._git_client = base_git
            else:
                self._git_client = InMemoryGitClient()
        return self._git_client

    @property
    def file_finder(self) -> FileFinder:
        """Get or create file finder service."""
        if self._file_finder is None:
            self._file_finder = FileFinder(self.filesystem)
        return self._file_finder

    @property
    def async_filesystem(self) -> AsyncFileSystemWrapper:
        """Get or create async filesystem wrapper."""
        if self._async_filesystem is None:
            self._async_filesystem = create_async_filesystem(self.filesystem)
        return self._async_filesystem

    @property
    def async_git_client(self) -> AsyncGitClientWrapper:
        """Get or create async git client wrapper."""
        if self._async_git_client is None:
            self._async_git_client = create_async_git_client(self.git_client)
        return self._async_git_client

    def get_dependencies(self) -> Dependencies:
        """Get all dependencies as a single object."""
        return Dependencies(
            filesystem=self.filesystem,
            git_client=self.git_client,
            file_finder=self.file_finder,
            async_filesystem=self.async_filesystem,
            async_git_client=self.async_git_client,
        )

    def reset(self) -> None:
        """Reset all cached dependencies."""
        self._filesystem = None
        self._git_client = None
        self._file_finder = None
        self._cache_manager = None
        self._async_filesystem = None
        self._async_git_client = None


# Global container instances
_production_container = DependencyContainer(use_production=True)
_test_container = DependencyContainer(use_production=False)


def get_production_container() -> DependencyContainer:
    """Get the production dependency container."""
    return _production_container


def get_test_container() -> DependencyContainer:
    """Get the test dependency container with in-memory implementations."""
    return _test_container


def get_container(use_production: bool = True) -> DependencyContainer:
    """Get the appropriate dependency container."""
    return _production_container if use_production else _test_container
