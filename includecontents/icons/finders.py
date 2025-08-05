"""
Static files finder for icon sprites.
Integrates icon sprite generation with Django's static file system.
"""

import os

from django.contrib.staticfiles.finders import BaseFinder
from django.core.files.storage import FileSystemStorage

from .builder import get_or_create_sprite, get_sprite_settings
from .storage import get_sprite_filename


class IconSpriteFinder(BaseFinder):
    """
    A staticfiles finder that generates icon sprites on-demand.

    This finder makes icon sprites work seamlessly with Django's static file system:
    - Sprites are generated when requested by collectstatic
    - Development server serves sprites on-demand
    - Works with any static file storage backend
    - Integrates with Django's static file versioning
    """

    def __init__(self, app_names=None, *args, **kwargs):
        self.locations = []
        self.storages = {}
        super().__init__(*args, **kwargs)

    def _get_sprite_path_prefix(self):
        """Get the configured sprite path prefix (e.g., 'icons/')."""
        sprite_settings = get_sprite_settings()
        storage_options = sprite_settings.get("storage_options", {})
        location = storage_options.get("location", "icons/")

        # Handle empty location - fallback to default
        if not location or not location.strip():
            location = "icons/"
        elif not location.endswith("/"):
            location += "/"

        return location

    def find(self, path, all=False, find_all=None):
        """
        Find icon sprite files by generating them on-demand.

        Args:
            path: Static file path to find
            all: DEPRECATED in Django 5.2 - use find_all instead
            find_all: If True, return all matches (currently unused as we only have one sprite per path)

        Returns:
            List of found files or empty list
        """
        # Handle Django 5.2 parameter deprecation: all -> find_all
        # The 'all' parameter is deprecated in Django 5.2 and will be removed in Django 6.1
        if find_all is None:
            find_all = all

        # Note: find_all parameter is kept for Django compatibility but not used
        # since we only ever have one sprite file per path

        # Only handle our sprite files
        if not self._is_sprite_path(path):
            return [] if find_all else None

        try:
            # Extract hash from path: icons/sprite-abc123.svg -> abc123
            expected_hash = self._extract_hash_from_path(path)

            # Generate the current sprite
            sprite_hash, sprite_content = get_or_create_sprite()

            # Check if the requested hash matches current sprite
            if sprite_hash == expected_hash:
                # Get the sprite filename and storage
                from .builder import get_icon_storage
                from .storage import get_sprite_filename

                sprite_filename = get_sprite_filename(sprite_hash)
                storage = get_icon_storage()

                # Try to get a file system path if the storage supports it
                if hasattr(storage, "path"):
                    # FileSystemIconStorage has a path() method
                    file_path = str(storage.path(sprite_filename))
                    if find_all:
                        return [file_path]
                    else:
                        return file_path
                else:
                    # For non-filesystem storage (like MemoryIconStorage),
                    # create a temporary file
                    import tempfile

                    temp_fd, temp_path = tempfile.mkstemp(
                        suffix=".svg", prefix="sprite-"
                    )
                    try:
                        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                            f.write(sprite_content)
                        if find_all:
                            return [temp_path]
                        else:
                            return temp_path
                    except Exception:
                        # Clean up temp file on error
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass
                        raise

        except Exception:
            # If anything goes wrong, just return empty - don't break static files
            pass

        return [] if find_all else None

    def list(self, ignore_patterns):
        """
        List all available sprite files and add source SVG files to ignore patterns.

        Args:
            ignore_patterns: Patterns to ignore - we'll add our source SVG files to this

        Yields:
            Tuples of (path, storage) for each available sprite
        """
        # Add source SVG files to ignore patterns so other finders don't pick them up
        self._add_source_files_to_ignore_patterns(ignore_patterns)

        try:
            sprite_hash, _ = get_or_create_sprite()
            if sprite_hash:
                sprite_filename = get_sprite_filename(sprite_hash)
                path_prefix = self._get_sprite_path_prefix()
                sprite_path = f"{path_prefix}{sprite_filename}"

                # Create a dummy storage for the list interface
                storage = FileSystemStorage()
                yield sprite_path, storage

        except Exception:
            # If sprite generation fails, don't yield anything
            pass

    def _add_source_files_to_ignore_patterns(self, ignore_patterns):
        """Add source SVG files to ignore patterns to prevent duplicate serving."""
        try:
            sprite_settings = get_sprite_settings()
            icon_definitions = sprite_settings.get("icons", [])

            # Find all local SVG file paths in the configuration
            for icon_def in icon_definitions:
                try:
                    if isinstance(icon_def, str):
                        # Direct file path like 'icons/logo.svg'
                        if ":" not in icon_def or icon_def.endswith(".svg"):
                            ignore_patterns.append(icon_def)
                    elif isinstance(icon_def, tuple) and len(icon_def) == 2:
                        # Tuple like ('logo', 'icons/brand.svg')
                        _, icon_name = icon_def
                        if ":" not in icon_name or icon_name.endswith(".svg"):
                            ignore_patterns.append(icon_name)
                except (ValueError, TypeError):
                    # Skip invalid definitions
                    continue

        except Exception:
            # If anything goes wrong, don't break the finder
            pass

    def _is_sprite_path(self, path):
        """Check if a path is for an icon sprite file."""
        path_prefix = self._get_sprite_path_prefix()
        sprite_prefix = f"{path_prefix}sprite-"

        # Check if path starts with our sprite prefix, ends with .svg, and is just the filename
        if not (path.startswith(sprite_prefix) and path.endswith(".svg")):
            return False

        # Extract the part after the sprite prefix
        remaining = path[len(sprite_prefix) :]

        # Should be just the hash + .svg, no additional path separators
        return (
            "/" not in remaining and len(remaining) > 4
        )  # Must have at least some hash chars + .svg

    def _extract_hash_from_path(self, path):
        """Extract sprite hash from a path like 'icons/sprite-abc123.svg'."""
        filename = os.path.basename(path)  # sprite-abc123.svg
        return filename.replace("sprite-", "").replace(".svg", "")  # abc123

    def _cleanup_old_sprites(self, storage, current_sprite_filename):
        """
        Clean up old sprite files that are no longer needed.

        Args:
            storage: Storage backend instance
            current_sprite_filename: Current sprite filename to keep
        """
        try:
            import glob

            if hasattr(storage, "location"):
                sprite_pattern = str(storage.location / "sprite-*.svg")
                existing_files = glob.glob(sprite_pattern)

                current_path = str(storage.path(current_sprite_filename))

                # Remove old sprite files (keep only the current one)
                for file_path in existing_files:
                    if file_path != current_path:
                        try:
                            os.unlink(file_path)
                        except OSError:
                            # Ignore errors when removing old files
                            pass
        except Exception:
            # Don't let cleanup errors break the finder
            pass
