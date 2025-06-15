"""Protocol definition for cache implementations.

This module defines the protocol for cache managers, enabling easy swapping
between SQLite-based and in-memory implementations for testing.
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            operation: The operation name (e.g., "file_tree", "git_diff")
            params: Parameters that uniquely identify the operation

        Returns:
            Cached value if found and not expired, None otherwise
        """
        ...

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
        ...

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
        ...

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        ...