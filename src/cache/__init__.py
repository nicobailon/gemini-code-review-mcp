"""Cache module for performance optimization."""

try:
    from .sqlite_cache import CacheEntry, CacheManager, get_cache_manager
except ImportError:
    from sqlite_cache import CacheEntry, CacheManager, get_cache_manager

__all__ = ["CacheManager", "CacheEntry", "get_cache_manager"]
