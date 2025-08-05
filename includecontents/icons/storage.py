"""
Storage interface and caching for icon sprites.
Now uses pluggable storage backends.
"""

from typing import Optional

from .builder import get_icon_storage


class IconMemoryCache:
    """
    Simple in-memory cache for icon sprites.
    Used for fast access and development.
    """

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[str]:
        """Get cached sprite content by hash."""
        return self._cache.get(key)

    def set(self, key: str, content: str) -> None:
        """Cache sprite content by hash."""
        self._cache[key] = content

    def clear(self) -> None:
        """Clear all cached content."""
        self._cache.clear()

    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._cache


# Global memory cache instance
_memory_cache = IconMemoryCache()


def get_sprite_filename(sprite_hash: str) -> str:
    """
    Generate sprite filename from hash.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        Filename for sprite
    """
    return f"sprite-{sprite_hash}.svg"


def cache_sprite(sprite_hash: str, content: str) -> None:
    """
    Store sprite content in memory cache.

    Args:
        sprite_hash: Hash of sprite content
        content: SVG sprite content
    """
    _memory_cache.set(sprite_hash, content)


def get_cached_sprite(sprite_hash: str) -> Optional[str]:
    """
    Retrieve sprite content from cache or storage.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        Sprite content or None if not found
    """
    # Try memory cache first
    content = _memory_cache.get(sprite_hash)
    if content is not None:
        return content

    # Try storage backend
    storage = get_icon_storage()
    filename = get_sprite_filename(sprite_hash)
    content = storage.open(filename)

    if content is not None:
        # Cache for faster access next time
        _memory_cache.set(sprite_hash, content)

    return content


def write_sprite_to_storage(sprite_hash: str, content: str) -> Optional[str]:
    """
    Write sprite content to storage backend.

    Args:
        sprite_hash: Hash of sprite content
        content: SVG sprite content

    Returns:
        Saved filename or None if failed
    """
    try:
        storage = get_icon_storage()
        filename = get_sprite_filename(sprite_hash)
        saved_name = storage.save(filename, content)
        return saved_name
    except Exception:
        return None


def read_sprite_from_storage(sprite_hash: str) -> Optional[str]:
    """
    Read sprite content from storage backend.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        Sprite content or None if not found
    """
    storage = get_icon_storage()
    filename = get_sprite_filename(sprite_hash)
    return storage.open(filename)


def is_sprite_on_storage(sprite_hash: str) -> bool:
    """
    Check if sprite exists in storage backend.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        True if sprite exists in storage
    """
    storage = get_icon_storage()
    filename = get_sprite_filename(sprite_hash)
    return storage.exists(filename)


def get_sprite_url(sprite_hash: str) -> Optional[str]:
    """
    Get URL for sprite file from storage backend.

    Args:
        sprite_hash: Hash of sprite content

    Returns:
        URL to sprite file or None if not available
    """
    storage = get_icon_storage()
    filename = get_sprite_filename(sprite_hash)

    if storage.exists(filename):
        return storage.url(filename)
    return None


def clear_sprite_cache() -> None:
    """Clear the memory cache."""
    _memory_cache.clear()
