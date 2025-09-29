"""
Test that IconSpriteFinder adds source SVG files to ignore patterns
to prevent duplicate serving by other finders.
"""

from unittest.mock import patch
from django.test import override_settings
from includecontents.icons.finders import IconSpriteFinder


def mock_iconify_api():
    """Mock Iconify API responses for tests."""

    def mock_fetch(prefix, names, api_base, cache_root=None, cache_static_path=None):
        if prefix == "mdi":
            return {"home": {"body": "<path/>", "viewBox": "0 0 24 24"}}
        elif prefix == "tabler":
            return {
                "house": {"body": "<rect/>", "viewBox": "0 0 24 24"},
                "user": {"body": "<circle/>", "viewBox": "0 0 24 24"},
            }
        return {}

    return mock_fetch


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "mdi:home",  # Iconify icon - shouldn't be ignored
            "icons/logo.svg",  # Local SVG - should be ignored
            (
                "brand",
                "assets/brand.svg",
            ),  # Local SVG with custom name - should be ignored
            (
                "nav-home",
                "tabler:house",
            ),  # Iconify with custom name - shouldn't be ignored
        ],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_ignore_patterns_added_for_local_svgs(mock_fetch):
    """Test that local SVG files are added to ignore patterns."""
    mock_fetch.side_effect = mock_iconify_api()

    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Should have added the local SVG files
    assert "icons/logo.svg" in ignore_patterns
    assert "assets/brand.svg" in ignore_patterns

    # Should not have added Iconify icons
    assert "mdi:home" not in ignore_patterns
    assert "tabler:house" not in ignore_patterns


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "mdi:home",
            "tabler:user",
        ],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_no_ignore_patterns_for_iconify_only(mock_fetch):
    """Test that no ignore patterns are added when only using Iconify icons."""
    mock_fetch.side_effect = mock_iconify_api()

    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Should not have added any patterns for Iconify icons without cache
    assert len(ignore_patterns) == 0


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "mdi:home",
            "tabler:user",
        ],
        "api_cache_static_path": ".icon_cache",
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_cache_directory_added_to_ignore_patterns(mock_fetch):
    """Test that cache directory is added to ignore patterns when configured."""
    mock_fetch.side_effect = mock_iconify_api()

    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Check that cache directory is in ignore patterns
    assert ".icon_cache/*" in ignore_patterns


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "mdi:home",
            "icons/logo.svg",
        ],
        "api_cache_static_path": ".icon_cache",
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_both_local_svgs_and_cache_ignored(mock_fetch):
    """Test that both local SVGs and cache directory are ignored when both are present."""
    mock_fetch.side_effect = mock_iconify_api()

    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Check that both are in ignore patterns
    assert "icons/logo.svg" in ignore_patterns
    assert ".icon_cache/*" in ignore_patterns


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "icons/nav/home.svg",
            "icons/nav/profile.svg",
            "logos/brand.svg",
            ("custom-logo", "logos/company.svg"),
        ],
    }
)
def test_ignore_patterns_for_nested_paths():
    """Test that nested SVG file paths are correctly added to ignore patterns."""
    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Should have added all the local SVG files
    expected_patterns = [
        "icons/nav/home.svg",
        "icons/nav/profile.svg",
        "logos/brand.svg",
        "logos/company.svg",
    ]

    for pattern in expected_patterns:
        assert pattern in ignore_patterns


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [],  # Empty configuration
    }
)
def test_empty_configuration_no_ignore_patterns():
    """Test that empty configuration doesn't add any ignore patterns."""
    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    assert len(ignore_patterns) == 0


def test_invalid_configuration_doesnt_break():
    """Test that invalid configurations don't break the ignore pattern logic."""
    finder = IconSpriteFinder()
    ignore_patterns = []

    # This should not raise an exception even with invalid config
    list(finder.list(ignore_patterns))

    # ignore_patterns might be empty or have some items, but shouldn't crash
    assert isinstance(ignore_patterns, list)


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [
            "icons/test.svg",  # Normal local file
            "assets/other.svg",  # Another local file
        ],
    }
)
def test_edge_cases_in_local_file_detection():
    """Test edge cases in detecting local vs remote icons."""
    finder = IconSpriteFinder()
    ignore_patterns = []

    # Call list() which should modify ignore_patterns
    list(finder.list(ignore_patterns))

    # Local SVG files should be added to ignore patterns
    assert "icons/test.svg" in ignore_patterns
    assert "assets/other.svg" in ignore_patterns
