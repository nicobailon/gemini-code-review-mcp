"""Tests for SQLite caching layer."""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gemini_code_review_mcp.cache.sqlite_cache import CacheEntry, CacheManager, get_cache_manager
from gemini_code_review_mcp.errors import CacheError


class TestCacheEntry:
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(key="test_key", value={"data": "test"}, ttl=300)
        assert entry.key == "test_key"
        assert entry.value == {"data": "test"}
        assert entry.ttl == 300
        assert isinstance(entry.timestamp, float)

    def test_cache_entry_expiration(self):
        """Test cache entry expiration check."""
        # Create entry that's already expired
        entry = CacheEntry(
            key="test_key", value="test", timestamp=time.time() - 1000, ttl=500
        )
        assert entry.is_expired() is True

        # Create fresh entry
        fresh_entry = CacheEntry(key="test_key", value="test", ttl=500)
        assert fresh_entry.is_expired() is False

    def test_cache_entry_serialization(self):
        """Test converting cache entry to/from dict."""
        original = CacheEntry(key="test_key", value={"nested": ["data", 123]}, ttl=600)

        # To dict
        data = original.to_dict()
        assert data["key"] == "test_key"
        assert data["value"] == {"nested": ["data", 123]}
        assert data["ttl"] == 600
        assert "timestamp" in data

        # From dict
        restored = CacheEntry.from_dict(data)
        assert restored.key == original.key
        assert restored.value == original.value
        assert restored.ttl == original.ttl
        assert restored.timestamp == original.timestamp


class TestCacheManager:
    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "test_cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a cache manager with temporary directory."""
        return CacheManager(cache_dir=temp_cache_dir, ttl=300)

    def test_cache_manager_initialization(self, temp_cache_dir):
        """Test cache manager initialization."""
        manager = CacheManager(cache_dir=temp_cache_dir)
        assert manager.db_path.exists()
        assert manager.ttl == 900  # Default TTL

        # Check database schema
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cache'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_generate_key(self, cache_manager):
        """Test cache key generation."""
        key1 = cache_manager._generate_key("file_tree", {"path": "/test"})
        key2 = cache_manager._generate_key("file_tree", {"path": "/test"})
        key3 = cache_manager._generate_key("file_tree", {"path": "/other"})

        # Same operation and params should generate same key
        assert key1 == key2
        # Different params should generate different key
        assert key1 != key3
        # Keys should be hex strings (SHA256)
        assert len(key1) == 64
        assert all(c in "0123456789abcdef" for c in key1)

    def test_set_and_get(self, cache_manager):
        """Test basic set and get operations."""
        test_data = {"files": ["a.py", "b.py"], "count": 2}

        # Set value
        cache_manager.set("file_tree", {"path": "/test"}, test_data)

        # Get value
        result = cache_manager.get("file_tree", {"path": "/test"})
        assert result == test_data

        # Get non-existent value
        result = cache_manager.get("file_tree", {"path": "/other"})
        assert result is None

    def test_ttl_handling(self, cache_manager):
        """Test TTL handling for cache entries."""
        # Set with custom TTL
        cache_manager.set(
            "git_diff", {"branch": "main"}, {"changes": []}, ttl=1  # 1 second
        )

        # Should be available immediately
        assert cache_manager.get("git_diff", {"branch": "main"}) is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired and return None
        assert cache_manager.get("git_diff", {"branch": "main"}) is None

    def test_invalidate_specific(self, cache_manager):
        """Test invalidating specific cache entries."""
        # Add multiple entries
        cache_manager.set("file_tree", {"path": "/a"}, ["a.py"])
        cache_manager.set("file_tree", {"path": "/b"}, ["b.py"])
        cache_manager.set("git_diff", {"branch": "main"}, {"changes": []})

        # Invalidate specific entry
        count = cache_manager.invalidate("file_tree", {"path": "/a"})
        assert count == 1

        # Check what remains
        assert cache_manager.get("file_tree", {"path": "/a"}) is None
        assert cache_manager.get("file_tree", {"path": "/b"}) is not None
        assert cache_manager.get("git_diff", {"branch": "main"}) is not None

    def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache entries."""
        # Add multiple entries
        cache_manager.set("file_tree", {"path": "/a"}, ["a.py"])
        cache_manager.set("file_tree", {"path": "/b"}, ["b.py"])
        cache_manager.set("git_diff", {"branch": "main"}, {"changes": []})

        # Invalidate all
        count = cache_manager.invalidate()
        assert count == 3

        # Check all are gone
        assert cache_manager.get("file_tree", {"path": "/a"}) is None
        assert cache_manager.get("file_tree", {"path": "/b"}) is None
        assert cache_manager.get("git_diff", {"branch": "main"}) is None

    def test_cleanup_expired(self, cache_manager):
        """Test cleaning up expired entries."""
        # Add entries with different TTLs
        cache_manager.set("entry1", {}, "data1", ttl=1)
        cache_manager.set("entry2", {}, "data2", ttl=1)
        cache_manager.set("entry3", {}, "data3", ttl=1000)  # Won't expire

        # Wait for some to expire
        time.sleep(1.1)

        # Cleanup
        count = cache_manager.cleanup_expired()
        assert count == 2

        # Check what remains
        stats = cache_manager.get_stats()
        assert stats["active_entries"] == 1
        assert cache_manager.get("entry3", {}) == "data3"

    def test_get_stats(self, cache_manager):
        """Test getting cache statistics."""
        # Start with empty cache
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["cache_size_bytes"] == 0

        # Add some entries
        cache_manager.set("entry1", {}, "small data")
        cache_manager.set("entry2", {}, {"larger": "data structure"})
        cache_manager.set("entry3", {}, "x" * 1000, ttl=1)

        # Wait for one to expire
        time.sleep(1.1)

        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 3
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 1
        assert stats["cache_size_bytes"] > 1000  # At least the large entry

    def test_database_error_handling(self, cache_manager):
        """Test handling of database errors."""
        # Mock sqlite3.connect to raise an error
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Database locked")

            with pytest.raises(CacheError, match="Database error"):
                cache_manager.get("test", {})

    def test_concurrent_access(self, cache_manager):
        """Test thread-safe concurrent access."""
        import threading

        results = []
        errors = []

        def worker(worker_id):
            try:
                # Each worker sets and gets its own data
                for i in range(10):
                    key_params = {"worker": worker_id, "iteration": i}
                    value = f"worker_{worker_id}_data_{i}"

                    cache_manager.set("concurrent_test", key_params, value)
                    retrieved = cache_manager.get("concurrent_test", key_params)

                    if retrieved != value:
                        errors.append(
                            f"Worker {worker_id}: expected {value}, got {retrieved}"
                        )

                results.append(worker_id)
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_async_operations(self, cache_manager):
        """Test async wrapper methods."""
        test_data = {"async": True, "data": [1, 2, 3]}

        # Async set
        await cache_manager.aset("async_test", {"id": 1}, test_data)

        # Async get
        result = await cache_manager.aget("async_test", {"id": 1})
        assert result == test_data

        # Async invalidate
        count = await cache_manager.ainvalidate("async_test", {"id": 1})
        assert count == 1

        # Verify it's gone
        result = await cache_manager.aget("async_test", {"id": 1})
        assert result is None

        # Add some entries for cleanup test
        await cache_manager.aset("expire1", {}, "data", ttl=1)
        await cache_manager.aset("expire2", {}, "data", ttl=1)

        # Wait and cleanup
        await asyncio.sleep(1.1)
        count = await cache_manager.acleanup_expired()
        assert count == 2

    def test_complex_data_types(self, cache_manager):
        """Test caching various data types."""
        test_cases = [
            # Simple types
            ("string", "test string"),
            ("number", 42),
            ("float", 3.14),
            ("boolean", True),
            ("null", None),
            # Collections
            ("list", [1, 2, 3, "four", None]),
            ("dict", {"nested": {"key": "value"}, "list": [1, 2]}),
            ("empty_list", []),
            ("empty_dict", {}),
            # Complex nested structures
            (
                "complex",
                {
                    "files": [
                        {"path": "/a/b.py", "size": 1024, "modified": True},
                        {"path": "/c/d.py", "size": 2048, "modified": False},
                    ],
                    "stats": {"total": 2, "modified": 1},
                    "metadata": None,
                },
            ),
        ]

        for data_type, value in test_cases:
            cache_manager.set("type_test", {"type": data_type}, value)
            result = cache_manager.get("type_test", {"type": data_type})
            assert result == value, f"Failed for type: {data_type}"


class TestGlobalCacheManager:
    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns singleton."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2

    def test_get_cache_manager_params(self, tmp_path):
        """Test get_cache_manager with custom parameters."""
        # Reset global
        import gemini_code_review_mcp.cache.sqlite_cache

        gemini_code_review_mcp.cache.sqlite_cache._cache_manager = None

        cache_dir = tmp_path / "custom_cache"
        manager = get_cache_manager(cache_dir=cache_dir, ttl=600)

        assert manager.ttl == 600
        assert cache_dir in manager.db_path.parents
