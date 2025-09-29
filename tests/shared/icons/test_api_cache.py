"""
Test API caching functionality for Iconify icons.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from includecontents.icons.builder import (
    fetch_iconify_icons,
    get_cached_iconify_icon,
    save_iconify_icon_to_cache,
    build_sprite,
)


def test_save_and_load_cached_icon():
    """Test saving and loading an icon from cache."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)

        # Icon data to cache
        icon_data = {
            "body": '<path d="M10 20v-6"/>',
            "viewBox": "0 0 24 24",
            "width": 24,
            "height": 24,
        }

        # Save to cache
        save_iconify_icon_to_cache("mdi", "home", icon_data, str(cache_root))

        # Verify file was created
        cache_file = cache_root / "mdi" / "home.json"
        assert cache_file.exists()

        # Verify content
        with open(cache_file) as f:
            saved_data = json.load(f)
        assert saved_data == icon_data


def test_get_cached_icon_not_found():
    """Test that get_cached_iconify_icon returns None when icon not in cache."""
    result = get_cached_iconify_icon("mdi", "nonexistent", ".icon_cache")
    assert result is None


def test_fetch_with_cache_hit():
    """Test that cached icons are used instead of API calls."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)
        cache_static_path = ".icon_cache"

        # Pre-populate cache
        cached_icon = {
            "body": '<path d="M10 20v-6"/>',
            "viewBox": "0 0 24 24",
            "width": 24,
            "height": 24,
        }
        save_iconify_icon_to_cache("mdi", "home", cached_icon, str(cache_root))

        # Mock find_source_svg to return our cache file
        with patch("includecontents.icons.builder.find_source_svg") as mock_find:
            cache_file = cache_root / "mdi" / "home.json"
            mock_find.return_value = str(cache_file)

            # Mock urlopen to ensure it's NOT called
            with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
                result = fetch_iconify_icons(
                    "mdi",
                    ["home"],
                    "https://api.iconify.design",
                    str(cache_root),
                    cache_static_path,
                )

                # Verify cached icon was returned
                assert result == {"home": cached_icon}

                # Verify API was NOT called
                mock_urlopen.assert_not_called()


def test_fetch_with_cache_miss():
    """Test that API is called when icon not in cache, and result is cached."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)
        cache_static_path = ".icon_cache"

        # Mock find_source_svg to return None (cache miss)
        with patch("includecontents.icons.builder.find_source_svg") as mock_find:
            mock_find.return_value = None

            # Mock API response
            api_response = {
                "icons": {
                    "home": {
                        "body": '<path d="M10 20v-6"/>',
                        "viewBox": "0 0 24 24",
                        "width": 24,
                        "height": 24,
                    }
                }
            }

            # Mock urlopen
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(api_response).encode()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None

            with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
                mock_urlopen.return_value = mock_response

                result = fetch_iconify_icons(
                    "mdi",
                    ["home"],
                    "https://api.iconify.design",
                    str(cache_root),
                    cache_static_path,
                )

                # Verify result
                expected = {
                    "home": {
                        "body": '<path d="M10 20v-6"/>',
                        "viewBox": "0 0 24 24",
                        "width": 24,
                        "height": 24,
                    }
                }
                assert result == expected

                # Verify API was called
                mock_urlopen.assert_called_once()

                # Verify icon was cached
                cache_file = cache_root / "mdi" / "home.json"
                assert cache_file.exists()


def test_fetch_mixed_cache_hit_miss():
    """Test fetching multiple icons with some cached and some not."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)
        cache_static_path = ".icon_cache"

        # Pre-populate cache with one icon
        cached_icon = {
            "body": '<path d="M10 20v-6"/>',
            "viewBox": "0 0 24 24",
            "width": 24,
            "height": 24,
        }
        save_iconify_icon_to_cache("mdi", "home", cached_icon, str(cache_root))

        # Mock find_source_svg to return cache file for "home" only
        def mock_find_side_effect(path):
            if "home.json" in path:
                return str(cache_root / "mdi" / "home.json")
            return None

        with patch("includecontents.icons.builder.find_source_svg") as mock_find:
            mock_find.side_effect = mock_find_side_effect

            # Mock API response for uncached icon
            api_response = {
                "icons": {
                    "account": {
                        "body": '<path d="M12 12c2.21"/>',
                        "viewBox": "0 0 24 24",
                        "width": 24,
                        "height": 24,
                    }
                }
            }

            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(api_response).encode()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None

            with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
                mock_urlopen.return_value = mock_response

                result = fetch_iconify_icons(
                    "mdi",
                    ["home", "account"],
                    "https://api.iconify.design",
                    str(cache_root),
                    cache_static_path,
                )

                # Verify both icons returned
                assert "home" in result
                assert "account" in result
                assert result["home"] == cached_icon

                # Verify API was called only for uncached icon
                mock_urlopen.assert_called_once()
                call_args = mock_urlopen.call_args[0][0]
                assert "icons=account" in call_args
                assert "icons=home" not in call_args


def test_build_sprite_with_cache():
    """Test that build_sprite uses cache when configured."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)
        cache_static_path = ".icon_cache"

        # Pre-populate cache
        cached_icon = {
            "body": '<path d="M10 20v-6"/>',
            "viewBox": "0 0 24 24",
            "width": 24,
            "height": 24,
        }
        save_iconify_icon_to_cache("mdi", "home", cached_icon, str(cache_root))

        # Mock find_source_svg
        with patch("includecontents.icons.builder.find_source_svg") as mock_find:
            cache_file = cache_root / "mdi" / "home.json"
            mock_find.return_value = str(cache_file)

            # Mock urlopen to ensure it's NOT called
            with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
                sprite = build_sprite(
                    ["mdi:home"],
                    cache_root=str(cache_root),
                    cache_static_path=cache_static_path,
                )

                # Verify sprite was built
                assert '<symbol id="home"' in sprite
                assert '<path d="M10 20v-6"/>' in sprite

                # Verify API was NOT called
                mock_urlopen.assert_not_called()


def test_cache_disabled_when_settings_none():
    """Test that caching is disabled when settings are None."""
    # Mock API response
    api_response = {
        "icons": {
            "home": {
                "body": '<path d="M10 20v-6"/>',
                "viewBox": "0 0 24 24",
            }
        }
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(api_response).encode()
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
        mock_urlopen.return_value = mock_response

        # Call without cache settings
        result = fetch_iconify_icons(
            "mdi",
            ["home"],
            "https://api.iconify.design",
            cache_root=None,
            cache_static_path=None,
        )

        # Verify result
        assert "home" in result

        # Verify API was called
        mock_urlopen.assert_called_once()


def test_cache_creates_directory_structure():
    """Test that cache creates the proper directory structure."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)

        # Save icons from different prefixes
        icon_data = {
            "body": '<path d="M10 20v-6"/>',
            "viewBox": "0 0 24 24",
            "width": 24,
            "height": 24,
        }

        save_iconify_icon_to_cache("mdi", "home", icon_data, str(cache_root))
        save_iconify_icon_to_cache("mdi", "account", icon_data, str(cache_root))
        save_iconify_icon_to_cache("tabler", "user", icon_data, str(cache_root))
        save_iconify_icon_to_cache("lucide", "star", icon_data, str(cache_root))

        # Verify directory structure
        assert (cache_root / "mdi").is_dir()
        assert (cache_root / "tabler").is_dir()
        assert (cache_root / "lucide").is_dir()

        assert (cache_root / "mdi" / "home.json").exists()
        assert (cache_root / "mdi" / "account.json").exists()
        assert (cache_root / "tabler" / "user.json").exists()
        assert (cache_root / "lucide" / "star.json").exists()


def test_cache_handles_invalid_json():
    """Test that invalid cache files are ignored and API is called."""
    with tempfile.TemporaryDirectory() as cache_dir:
        cache_root = Path(cache_dir)
        cache_static_path = ".icon_cache"

        # Create invalid cache file
        cache_subdir = cache_root / "mdi"
        cache_subdir.mkdir(parents=True)
        cache_file = cache_subdir / "home.json"
        cache_file.write_text("INVALID JSON")

        # Mock find_source_svg to return invalid cache file
        with patch("includecontents.icons.builder.find_source_svg") as mock_find:
            mock_find.return_value = str(cache_file)

            # Mock API response
            api_response = {
                "icons": {
                    "home": {
                        "body": '<path d="M10 20v-6"/>',
                        "viewBox": "0 0 24 24",
                    }
                }
            }

            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(api_response).encode()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None

            with patch("includecontents.icons.builder.urlopen") as mock_urlopen:
                mock_urlopen.return_value = mock_response

                result = fetch_iconify_icons(
                    "mdi",
                    ["home"],
                    "https://api.iconify.design",
                    str(cache_root),
                    cache_static_path,
                )

                # Verify API was called (cache was invalid)
                mock_urlopen.assert_called_once()

                # Verify result
                assert "home" in result
