"""
Django cache integration for icon sprites.
"""

from typing import Optional

from django.core.cache import cache
from django.conf import settings


class SpriteCache:
    """
    Sprite caching using Django's cache framework.

    This provides a simple interface to Django's cache system
    with appropriate key prefixes and timeouts for icon sprites.
    """

    def __init__(self, key_prefix: str = "icon_sprite", timeout: Optional[int] = None):
        """
        Initialize the sprite cache.

        Args:
            key_prefix: Prefix for all cache keys
            timeout: Cache timeout in seconds (None = use default)
        """
        self.key_prefix = key_prefix
        # Use configured timeout or Django's default
        self.timeout = timeout or getattr(settings, "ICON_SPRITE_CACHE_TIMEOUT", 3600)

    def _make_key(self, sprite_hash: str) -> str:
        """Create a cache key for a sprite hash."""
        return f"{self.key_prefix}:{sprite_hash}"

    def get(self, sprite_hash: str) -> Optional[str]:
        """
        Get sprite content from cache.

        Args:
            sprite_hash: Sprite hash identifier

        Returns:
            Cached sprite content or None if not found
        """
        return cache.get(self._make_key(sprite_hash))

    def set(self, sprite_hash: str, content: str) -> None:
        """
        Store sprite content in cache.

        Args:
            sprite_hash: Sprite hash identifier
            content: SVG sprite content to cache
        """
        cache.set(self._make_key(sprite_hash), content, self.timeout)

    def delete(self, sprite_hash: str) -> None:
        """
        Remove a sprite from cache.

        Args:
            sprite_hash: Sprite hash identifier
        """
        cache.delete(self._make_key(sprite_hash))

    def clear(self) -> None:
        """
        Clear all sprite caches.

        Note: This only works reliably with cache backends that support
        delete_pattern (like Redis). For other backends, it's a no-op.
        """
        try:
            # Try to use delete_pattern if available (Redis, etc.)
            cache.delete_pattern(f"{self.key_prefix}:*")
        except AttributeError:
            # Fallback: cache backend doesn't support pattern deletion
            # In production, you'd typically use cache versioning instead
            pass


# Global sprite cache instance
sprite_cache = SpriteCache()
