"""
Static files finder for icon sprites.
Integrates icon sprite generation with Django's static file system.
"""

import os

from django.contrib.staticfiles.finders import BaseFinder
from django.core.files.storage import FileSystemStorage

from .builder import get_or_create_sprite, get_sprite_settings, get_sprite_filename
from .exceptions import IconBuildError


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
        """Get the sprite path prefix (always 'icons/')."""
        return "icons/"

    def find(self, path, find_all=False, **kwargs):
        """
        Find icon sprite files by generating them on-demand.

        Args:
            path: Static file path to find
            find_all: If True, return all matches (currently unused as we only have one sprite per path)
            **kwargs: For backward compatibility with Django < 5.2 (handles 'all' parameter)

        Returns:
            String path if found (when find_all=False), list of paths (when find_all=True), or None/[]
        """
        # Handle Django < 5.2 compatibility where 'all' was used instead of 'find_all'
        if "all" in kwargs:
            find_all = kwargs["all"]

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
                # Create a temporary file to serve the sprite
                import tempfile

                temp_fd, temp_path = tempfile.mkstemp(suffix=".svg", prefix="sprite-")
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

        except Exception as e:
            # Log the error but don't break static file serving
            # When icons are misconfigured, we should fail silently and let
            # Django return a proper 404 rather than breaking the entire
            # static file serving system
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Icon sprite generation failed for {path}: {e}")

            # IMPORTANT: Return a fake file path to stop Django from continuing
            # to other finders and wrapping None in a list (Django 5.2 bug).
            # This will cause a proper 404 error instead of a TypeError.
            if not find_all:
                # Return a non-existent file path that will trigger a 404
                import tempfile

                # Create a path that doesn't exist
                return os.path.join(tempfile.gettempdir(), "sprite-error-404.svg")
            return []

        # Return None/[] when we don't have a matching sprite
        # This is the normal case when the hash doesn't match
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

        except Exception as e:
            # During collectstatic, we want to fail loudly
            # This is a configuration error that should be fixed
            if isinstance(e, IconBuildError):
                raise  # Re-raise our custom exception as-is
            raise IconBuildError(
                f"Failed to generate icon sprite during collectstatic: {e}"
            ) from e

    def _add_source_files_to_ignore_patterns(self, ignore_patterns):
        """Add source SVG files and cache files to ignore patterns to prevent duplicate serving."""
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

            # Also ignore cached icon files if cache is configured
            cache_static_path = sprite_settings.get("api_cache_static_path")
            if cache_static_path:
                # Add the entire cache directory to ignore patterns
                # This prevents cached JSON files from being served as static files
                ignore_patterns.append(f"{cache_static_path}/*")

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
