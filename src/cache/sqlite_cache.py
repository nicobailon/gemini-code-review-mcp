"""SQLite-based caching layer for file tree and Git metadata.

This module provides a thread-safe caching mechanism to avoid redundant
filesystem and Git operations, improving performance for repeated operations.
"""

import asyncio
import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

try:
    from ..errors import CacheError
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from errors import CacheError


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""

    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: int = 900  # 15 minutes default

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class CacheManager:
    """Thread-safe SQLite cache manager for file tree and Git metadata."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 900):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache database. If None, uses temp directory.
            ttl: Default time-to-live for cache entries in seconds.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "gemini-code-review"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "metadata_cache.db"
        self.ttl = ttl
        self._lock = Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    ttl INTEGER NOT NULL
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON cache(timestamp)
            """
            )
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            raise CacheError(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def _generate_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from operation and parameters."""
        # Create a deterministic string representation
        param_str = json.dumps(params, sort_keys=True)
        key_str = f"{operation}:{param_str}"

        # Hash for consistent length and avoid special characters
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            operation: The operation name (e.g., "file_tree", "git_diff")
            params: Parameters that uniquely identify the operation

        Returns:
            Cached value if found and not expired, None otherwise
        """
        key = self._generate_key(operation, params)

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT value, timestamp, ttl FROM cache WHERE key = ?", (key,)
                )
                row = cursor.fetchone()

                if row:
                    entry = CacheEntry(
                        key=key,
                        value=json.loads(row["value"]),
                        timestamp=row["timestamp"],
                        ttl=row["ttl"],
                    )

                    if not entry.is_expired():
                        return entry.value
                    else:
                        # Clean up expired entry
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                        conn.commit()

        return None

    def set(
        self,
        operation: str,
        params: Dict[str, Any],
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store a value in cache.

        Args:
            operation: The operation name
            params: Parameters that uniquely identify the operation
            value: The value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        key = self._generate_key(operation, params)
        entry = CacheEntry(
            key=key, value=value, timestamp=time.time(), ttl=ttl or self.ttl
        )

        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache (key, value, timestamp, ttl)
                    VALUES (?, ?, ?, ?)
                    """,
                    (entry.key, json.dumps(entry.value), entry.timestamp, entry.ttl),
                )
                conn.commit()

    def invalidate(
        self, operation: Optional[str] = None, params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            operation: If provided, only invalidate entries for this operation
            params: If provided with operation, only invalidate specific entry

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            with self._get_connection() as conn:
                if operation and params:
                    # Invalidate specific entry
                    key = self._generate_key(operation, params)
                    cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                elif operation:
                    # Invalidate all entries for an operation (using prefix matching)
                    # Since we hash keys, we can't do prefix matching directly
                    # Instead, we'd need to store operation type separately
                    # For now, this will clear all cache
                    cursor = conn.execute("DELETE FROM cache")
                else:
                    # Clear entire cache
                    cursor = conn.execute("DELETE FROM cache")

                conn.commit()
                return cursor.rowcount

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()

        with self._lock:
            with self._get_connection() as conn:
                # First, get all entries to check expiration
                cursor = conn.execute("SELECT key, timestamp, ttl FROM cache")
                expired_keys: List[str] = []

                for row in cursor:
                    entry_age = current_time - row["timestamp"]
                    if entry_age > row["ttl"]:
                        expired_keys.append(row["key"])

                # Delete expired entries
                if expired_keys:
                    placeholders = ",".join("?" * len(expired_keys))
                    cursor = conn.execute(
                        f"DELETE FROM cache WHERE key IN ({placeholders})", expired_keys
                    )
                    conn.commit()
                    return cursor.rowcount

                return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as total FROM cache")
                total = cursor.fetchone()["total"]

                cursor = conn.execute("SELECT SUM(LENGTH(value)) as size FROM cache")
                size = cursor.fetchone()["size"] or 0

                # Check expired entries
                current_time = time.time()
                cursor = conn.execute("SELECT timestamp, ttl FROM cache")
                expired = sum(
                    1 for row in cursor if current_time - row["timestamp"] > row["ttl"]
                )

                return {
                    "total_entries": total,
                    "expired_entries": expired,
                    "active_entries": total - expired,
                    "cache_size_bytes": size,
                    "db_path": str(self.db_path),
                }

    async def aget(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """Async wrapper for get operation."""
        return await asyncio.to_thread(self.get, operation, params)

    async def aset(
        self,
        operation: str,
        params: Dict[str, Any],
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Async wrapper for set operation."""
        await asyncio.to_thread(self.set, operation, params, value, ttl)

    async def ainvalidate(
        self, operation: Optional[str] = None, params: Optional[Dict[str, Any]] = None
    ) -> int:
        """Async wrapper for invalidate operation."""
        return await asyncio.to_thread(self.invalidate, operation, params)

    async def acleanup_expired(self) -> int:
        """Async wrapper for cleanup operation."""
        return await asyncio.to_thread(self.cleanup_expired)


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_dir: Optional[Path] = None, ttl: int = 900) -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(cache_dir, ttl)
    return _cache_manager
