"""
Storage backends for icon sprites.
Follows Django's storage API patterns for consistency.
"""

import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


class BaseIconStorage(ABC):
    """
    Abstract base class for icon storage backends.
    """

    @abstractmethod
    def save(self, name: str, content: str) -> str:
        """
        Save sprite content and return the saved filename.

        Args:
            name: Filename to save
            content: Sprite content

        Returns:
            Saved filename (may differ from input name)
        """
        pass

    @abstractmethod
    def open(self, name: str) -> Optional[str]:
        """
        Open and return sprite content.

        Args:
            name: Filename to open

        Returns:
            File content or None if not found
        """
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        Check if sprite file exists.

        Args:
            name: Filename to check

        Returns:
            True if file exists
        """
        pass

    @abstractmethod
    def url(self, name: str) -> Optional[str]:
        """
        Get URL for sprite file.

        Args:
            name: Filename

        Returns:
            URL or None if not available
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete sprite file.

        Args:
            name: Filename to delete

        Returns:
            True if deleted successfully
        """
        pass


@deconstructible
class FileSystemIconStorage(BaseIconStorage):
    """
    File system storage backend for icon sprites.
    """

    def __init__(self, location: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize file system storage.

        Args:
            location: Directory path for storage (default: BASE_DIR/static/includecontents/icons/)
            base_url: Base URL for serving files (default: /static/includecontents/icons/)
        """
        if location is None:
            location = (
                Path(getattr(settings, "BASE_DIR", "."))
                / "static"
                / "includecontents"
                / "icons"
            )

        if base_url is None:
            base_url = "/static/includecontents/icons/"

        self.location = Path(location)
        self.base_url = base_url.rstrip("/") + "/"

        # Ensure directory exists
        self.location.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, content: str) -> str:
        """Save sprite content to file system."""
        file_path = self.location / name

        # Use atomic write: write to temp file, then rename
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.location, delete=False, suffix=".tmp"
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        # Atomic rename
        temp_path.rename(file_path)
        return name

    def open(self, name: str) -> Optional[str]:
        """Open and return sprite content."""
        file_path = self.location / name

        try:
            return file_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return None

    def exists(self, name: str) -> bool:
        """Check if sprite file exists."""
        file_path = self.location / name
        return file_path.exists() and file_path.is_file()

    def url(self, name: str) -> Optional[str]:
        """Get URL for sprite file."""
        if not self.exists(name):
            return None
        return urljoin(self.base_url, name)

    def delete(self, name: str) -> bool:
        """Delete sprite file."""
        file_path = self.location / name

        try:
            file_path.unlink()
            return True
        except (FileNotFoundError, OSError):
            return False

    def path(self, name: str) -> Path:
        """Get full path for a filename."""
        return self.location / name


@deconstructible
class MemoryIconStorage(BaseIconStorage):
    """
    In-memory storage backend for development and testing.
    """

    def __init__(self):
        """Initialize memory storage."""
        self._storage = {}

    def save(self, name: str, content: str) -> str:
        """Save sprite content to memory."""
        self._storage[name] = content
        return name

    def open(self, name: str) -> Optional[str]:
        """Open and return sprite content from memory."""
        return self._storage.get(name)

    def exists(self, name: str) -> bool:
        """Check if sprite exists in memory."""
        return name in self._storage

    def url(self, name: str) -> Optional[str]:
        """Memory storage doesn't provide URLs."""
        return None

    def delete(self, name: str) -> bool:
        """Delete sprite from memory."""
        if name in self._storage:
            del self._storage[name]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored sprites."""
        self._storage.clear()


@deconstructible
class DjangoFileIconStorage(BaseIconStorage):
    """
    Storage backend that uses Django's default file storage.
    Useful for cloud storage backends (S3, GCS, etc.).
    """

    def __init__(self, storage: Optional[Storage] = None, location: str = "icons/"):
        """
        Initialize Django file storage wrapper.

        Args:
            storage: Django storage instance (default: default_storage)
            location: Directory prefix within the storage
        """
        if storage is None:
            from django.core.files.storage import default_storage

            storage = default_storage

        self.storage = storage
        self.location = location.rstrip("/") + "/" if location else ""

    def _get_name(self, name: str) -> str:
        """Get full storage name with location prefix."""
        return self.location + name

    def save(self, name: str, content: str) -> str:
        """Save sprite content using Django storage."""
        from django.core.files.base import ContentFile

        full_name = self._get_name(name)
        content_file = ContentFile(content.encode("utf-8"))
        saved_name = self.storage.save(full_name, content_file)

        # Return just the filename part
        return (
            saved_name[len(self.location) :]
            if saved_name.startswith(self.location)
            else saved_name
        )

    def open(self, name: str) -> Optional[str]:
        """Open and return sprite content from Django storage."""
        full_name = self._get_name(name)

        try:
            with self.storage.open(full_name, "r") as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return None

    def exists(self, name: str) -> bool:
        """Check if sprite exists in Django storage."""
        full_name = self._get_name(name)
        return self.storage.exists(full_name)

    def url(self, name: str) -> Optional[str]:
        """Get URL for sprite file from Django storage."""
        if not self.exists(name):
            return None

        full_name = self._get_name(name)
        try:
            return self.storage.url(full_name)
        except (NotImplementedError, ValueError):
            return None

    def delete(self, name: str) -> bool:
        """Delete sprite from Django storage."""
        full_name = self._get_name(name)

        try:
            self.storage.delete(full_name)
            return True
        except (FileNotFoundError, OSError):
            return False


# Default storage instance
default_icon_storage = FileSystemIconStorage()
