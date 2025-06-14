"""Tests for cached filesystem and Git client implementations."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cache import CacheManager
from src.interfaces import (
    AsyncFileSystemWrapper,
    AsyncGitClientWrapper,
    CachedFileSystem,
    CachedGitClient,
    GitFileChange,
    InMemoryFileSystem,
    InMemoryGitClient,
)


class TestCachedFileSystem:
    @pytest.fixture
    def base_fs(self):
        """Create base filesystem."""
        fs = InMemoryFileSystem()
        fs.mkdir("/test", parents=True)
        fs.write_text("/test/file.txt", "content")
        return fs

    @pytest.fixture
    def cache_manager(self):
        """Create mock cache manager."""
        return MagicMock(spec=CacheManager)

    @pytest.fixture
    def cached_fs(self, base_fs, cache_manager):
        """Create cached filesystem."""
        return CachedFileSystem(base_fs, cache_manager)

    def test_read_text_cache_hit(self, cached_fs, cache_manager):
        """Test reading text with cache hit."""
        cache_manager.get.return_value = "cached content"

        result = cached_fs.read_text("/test/file.txt")

        assert result == "cached content"
        cache_manager.get.assert_called_once_with(
            "fs_read_text", {"path": "/test/file.txt", "encoding": "utf-8"}
        )
        cache_manager.set.assert_not_called()

    def test_read_text_cache_miss(self, cached_fs, cache_manager):
        """Test reading text with cache miss."""
        cache_manager.get.return_value = None

        result = cached_fs.read_text("/test/file.txt")

        assert result == "content"
        cache_manager.get.assert_called_once()
        cache_manager.set.assert_called_once_with(
            "fs_read_text", {"path": "/test/file.txt", "encoding": "utf-8"}, "content"
        )

    def test_write_text_invalidates_cache(self, cached_fs, cache_manager):
        """Test that writing text invalidates cache."""
        cached_fs.write_text("/test/file.txt", "new content")

        cache_manager.invalidate.assert_called_once_with(
            "fs_read_text", {"path": "/test/file.txt", "encoding": "utf-8"}
        )

    def test_list_dir_caching(self, cached_fs, cache_manager, base_fs):
        """Test directory listing caching."""
        # Add more files
        base_fs.write_text("/test/file2.txt", "content2")

        # Cache miss
        cache_manager.get.return_value = None

        result = cached_fs.list_dir("/test")

        assert len(result) == 2
        cache_manager.set.assert_called_once()
        # Check that paths are cached as strings
        cached_data = cache_manager.set.call_args[0][2]
        assert all(isinstance(p, str) for p in cached_data)

    def test_list_dir_cache_hit(self, cached_fs, cache_manager):
        """Test directory listing with cache hit."""
        cache_manager.get.return_value = ["/test/cached1.txt", "/test/cached2.txt"]

        result = cached_fs.list_dir("/test")

        assert len(result) == 2
        assert all(isinstance(p, Path) for p in result)
        assert result[0] == Path("/test/cached1.txt")

    def test_glob_caching(self, cached_fs, cache_manager, base_fs):
        """Test glob pattern caching."""
        base_fs.write_text("/test/file.py", "python")

        cache_manager.get.return_value = None

        result = cached_fs.glob("/test", "*.txt")

        assert len(result) == 1
        assert result[0] == Path("/test/file.txt")
        cache_manager.set.assert_called_once()

    def test_mkdir_invalidates_parent_cache(self, cached_fs, cache_manager):
        """Test that mkdir invalidates parent directory cache."""
        cached_fs.mkdir("/test/subdir")

        cache_manager.invalidate.assert_called_once_with(
            "fs_list_dir", {"path": "/test"}
        )

    def test_remove_invalidates_caches(self, cached_fs, cache_manager):
        """Test that remove invalidates multiple caches."""
        cached_fs.remove("/test/file.txt")

        # Should invalidate both file content and parent directory
        assert cache_manager.invalidate.call_count == 2
        calls = cache_manager.invalidate.call_args_list
        assert any(
            call[0] == ("fs_read_text", {"path": "/test/file.txt", "encoding": "utf-8"})
            for call in calls
        )
        assert any(call[0] == ("fs_list_dir", {"path": "/test"}) for call in calls)

    def test_non_cached_operations(self, cached_fs, cache_manager, base_fs):
        """Test that fast operations are not cached."""
        # These should not interact with cache
        cached_fs.exists("/test/file.txt")
        cached_fs.is_file("/test/file.txt")
        cached_fs.is_dir("/test")
        cached_fs.get_cwd()
        cached_fs.resolve("/test/file.txt")

        cache_manager.get.assert_not_called()
        cache_manager.set.assert_not_called()

    def test_invalidate_cache_specific(self, cached_fs, cache_manager):
        """Test invalidating specific cache operations."""
        cache_manager.invalidate.return_value = 3

        count = cached_fs.invalidate_cache("read_text")

        assert count == 3
        cache_manager.invalidate.assert_called_once_with("fs_read_text")

    def test_invalidate_cache_all(self, cached_fs, cache_manager):
        """Test invalidating all cache operations."""
        cache_manager.invalidate.return_value = 1

        count = cached_fs.invalidate_cache()

        assert count == 3  # read_text + list_dir + glob
        assert cache_manager.invalidate.call_count == 3


class TestCachedGitClient:
    @pytest.fixture
    def base_git(self):
        """Create base Git client."""
        git = InMemoryGitClient()
        git.setup_repo("/repo", current_branch="main")
        return git

    @pytest.fixture
    def cache_manager(self):
        """Create mock cache manager."""
        return MagicMock(spec=CacheManager)

    @pytest.fixture
    def cached_git(self, base_git, cache_manager):
        """Create cached Git client."""
        return CachedGitClient(base_git, cache_manager)

    def test_get_current_branch_short_ttl(self, cached_git, cache_manager):
        """Test that current branch is cached with short TTL."""
        cache_manager.get.return_value = None

        result = cached_git.get_current_branch(Path("/repo"))

        assert result == "main"
        cache_manager.set.assert_called_once_with(
            "git_current_branch", {"repo_path": "/repo"}, "main", ttl=60  # Short TTL
        )

    def test_get_changed_files_caching(self, cached_git, cache_manager, base_git):
        """Test changed files caching."""
        changes = [
            GitFileChange("file1.py", "Modified", 10, 5),
            GitFileChange("file2.py", "Added", 20, 0),
        ]
        base_git.setup_repo("/repo", changes=changes)

        cache_manager.get.return_value = None

        result = cached_git.get_changed_files(Path("/repo"))

        assert len(result) == 2
        # Check cache data format
        cache_data = cache_manager.set.call_args[0][2]
        assert all(isinstance(item, dict) for item in cache_data)
        assert cache_data[0]["file_path"] == "file1.py"

    def test_get_changed_files_cache_hit(self, cached_git, cache_manager):
        """Test changed files with cache hit."""
        cache_data = [
            {
                "file_path": "cached1.py",
                "status": "Modified",
                "additions": 5,
                "deletions": 2,
                "old_path": None,
            },
            {
                "file_path": "cached2.py",
                "status": "Added",
                "additions": 10,
                "deletions": 0,
                "old_path": None,
            },
        ]
        cache_manager.get.return_value = cache_data

        result = cached_git.get_changed_files(Path("/repo"))

        assert len(result) == 2
        assert all(isinstance(change, GitFileChange) for change in result)
        assert result[0].file_path == "cached1.py"

    def test_get_file_diff_caching(self, cached_git, cache_manager):
        """Test file diff caching."""
        cache_manager.get.return_value = None

        result = cached_git.get_file_diff(Path("/repo"), "file.py")

        # InMemoryGitClient returns a non-empty diff
        assert "diff --git" in result
        cache_manager.set.assert_called_once()

    def test_get_remote_url_caching(self, cached_git, cache_manager, base_git):
        """Test remote URL caching."""
        # First call - cache miss
        cache_manager.get.return_value = None

        result = cached_git.get_remote_url(Path("/repo"))

        # InMemoryGitClient returns a URL
        assert result == "https://github.com/test/repo.git"
        cache_manager.set.assert_called_once_with(
            "git_remote_url",
            {"repo_path": "/repo", "remote": "origin"},
            "https://github.com/test/repo.git",
        )

    def test_get_remote_url_cache_hit_none(self, cached_git, cache_manager):
        """Test cache hit with None value."""
        cache_manager.get.return_value = "None"

        result = cached_git.get_remote_url(Path("/repo"))

        assert result is None

    def test_non_cached_operations(self, cached_git, cache_manager):
        """Test that fast operations are not cached."""
        cached_git.is_git_repo(Path("/repo"))

        cache_manager.get.assert_not_called()
        cache_manager.set.assert_not_called()

    def test_invalidate_cache_specific_repo(self, cached_git, cache_manager):
        """Test invalidating cache for specific repository."""
        cache_manager.invalidate.return_value = 1

        count = cached_git.invalidate_cache("changed_files", Path("/repo"))

        assert count == 1
        cache_manager.invalidate.assert_called_once_with(
            "git_changed_files", {"repo_path": "/repo"}
        )


class TestAsyncWrappers:
    @pytest.mark.asyncio
    async def test_async_filesystem_wrapper(self):
        """Test async filesystem wrapper."""
        base_fs = InMemoryFileSystem()
        base_fs.mkdir("/test", parents=True)
        base_fs.write_text("/test/file.txt", "async content")

        async_fs = AsyncFileSystemWrapper(base_fs)

        # Test various async operations
        assert await async_fs.exists("/test/file.txt") is True
        assert await async_fs.is_file("/test/file.txt") is True
        assert await async_fs.is_dir("/test") is True

        content = await async_fs.read_text("/test/file.txt")
        assert content == "async content"

        files = await async_fs.list_dir("/test")
        assert len(files) == 1

        await async_fs.write_text("/test/new.txt", "new async content")
        assert base_fs.exists("/test/new.txt")

    @pytest.mark.asyncio
    async def test_async_git_client_wrapper(self):
        """Test async Git client wrapper."""
        base_git = InMemoryGitClient()
        base_git.setup_repo("/repo", current_branch="async-branch")

        async_git = AsyncGitClientWrapper(base_git)

        # Test various async operations
        assert await async_git.is_git_repo(Path("/repo")) is True

        branch = await async_git.get_current_branch(Path("/repo"))
        assert branch == "async-branch"

        changes = await async_git.get_changed_files(Path("/repo"))
        assert isinstance(changes, list)

        commits = await async_git.get_commits(Path("/repo"))
        assert isinstance(commits, list)

    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self):
        """Test concurrent async operations."""
        base_fs = InMemoryFileSystem()
        base_fs.mkdir("/test", parents=True)
        for i in range(5):
            base_fs.write_text(f"/test/file{i}.txt", f"content{i}")

        async_fs = AsyncFileSystemWrapper(base_fs)

        # Run multiple reads concurrently
        tasks = [async_fs.read_text(f"/test/file{i}.txt") for i in range(5)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for i, content in enumerate(results):
            assert content == f"content{i}"
