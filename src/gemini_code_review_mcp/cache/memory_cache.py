"""In-memory cache implementation for testing.

This module provides a simple in-memory cache that implements the CacheProtocol,
useful for unit tests to avoid touching SQLite.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..interfaces.cache_protocol import CacheProtocol


@dataclass
class MemoryCacheEntry:
    """Represents an in-memory cache entry."""

    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: int = 900  # 15 minutes default

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class InMemoryCache(CacheProtocol):
    """In-memory cache implementation for testing."""

    def __init__(self, ttl: int = 900):
        """
        Initialize the in-memory cache.

        Args:
            ttl: Default time-to-live for cache entries in seconds.
        """
        self.ttl = ttl
        self._cache: Dict[str, MemoryCacheEntry] = {}

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

        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                # Clean up expired entry
                del self._cache[key]

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
        self._cache[key] = MemoryCacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl or self.ttl,
        )

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
        if operation and params:
            # Invalidate specific entry
            key = self._generate_key(operation, params)
            if key in self._cache:
                del self._cache[key]
                return 1
            return 0
        else:
            # Clear entire cache (operation-specific clearing not supported in simple impl)
            count = len(self._cache)
            self._cache.clear()
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._cache)
        expired = sum(1 for entry in self._cache.values() if entry.is_expired())

        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
            "cache_size_bytes": sum(
                len(json.dumps(entry.value)) for entry in self._cache.values()
            ),
            "db_path": "memory://",
        }