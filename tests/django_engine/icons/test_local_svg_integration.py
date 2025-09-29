"""
Test that local SVG files are properly loaded and included in sprites.
"""

from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons.builder import build_sprite, load_local_svg


def test_load_local_svg_from_static_files():
    """Test that local SVG files can be loaded from Django's static files."""
    # Load an actual test SVG file
    svg_data = load_local_svg("icons/custom-home.svg")

    # Verify the SVG data structure
    assert "body" in svg_data
    assert "viewBox" in svg_data

    # Our test SVG has specific content
    assert "M12 3l9 7v11" in svg_data["body"]  # Part of the path
    assert svg_data["viewBox"] == "0 0 24 24"


def test_build_sprite_with_local_svgs():
    """Test building a sprite with only local SVG files."""
    icons = [
        "icons/custom-home.svg",
        "icons/custom-star.svg",
    ]

    sprite = build_sprite(icons)

    # Verify sprite structure
    assert "<svg" in sprite
    assert 'style="display:none"' in sprite

    # Verify both icons are included as symbols
    # Component names are extracted from filenames
    assert '<symbol id="custom-home"' in sprite
    assert '<symbol id="custom-star"' in sprite

    # Verify the actual SVG content is included
    assert "M12 3l9 7v11" in sprite  # custom-home path
    assert "M10 1l2.5 6.5h6.5" in sprite  # custom-star path


def test_build_sprite_with_mixed_sources():
    """Test building a sprite with both local SVGs and Iconify icons."""
    from unittest.mock import patch

    def mock_fetch(prefix, names, api_base, cache_root=None, cache_static_path=None):
        if prefix == "mdi":
            return {"home": {"body": '<path d="M10 20v-6"/>', "viewBox": "0 0 24 24"}}
        return {}

    with patch(
        "includecontents.icons.builder.fetch_iconify_icons", side_effect=mock_fetch
    ):
        icons = [
            "mdi:home",
            "icons/custom-star.svg",
        ]

        sprite = build_sprite(icons)

        # Verify both icon types are included
        # Component names are properly extracted
        assert '<symbol id="home"' in sprite  # mdi:home -> home
        assert (
            '<symbol id="custom-star"' in sprite
        )  # icons/custom-star.svg -> custom-star

        # Verify content from both sources
        assert "M10 20v-6" in sprite  # Iconify icon
        assert "M10 1l2.5 6.5h6.5" in sprite  # Local SVG


def test_render_local_svg_icon():
    """Test that local SVG icons render correctly in templates."""
    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": [
                "icons/custom-home.svg",
                ("star", "icons/custom-star.svg"),
            ],
        }
    ):
        # Test direct reference
        template_str = '<icon:custom-home class="home-icon" />'
        template = CustomTemplate(template_str)
        result = template.render(Context())

        assert '<svg class="home-icon">' in result
        assert '#custom-home">' in result

        # Test tuple with custom name
        template_str = '<icon:star class="star-icon" />'
        template = CustomTemplate(template_str)
        result = template.render(Context())

        assert '<svg class="star-icon">' in result
        assert '#star">' in result


def test_local_svg_with_invalid_path_fails():
    """Test that referencing non-existent local SVG files fails loudly."""
    import pytest
    from includecontents.icons.exceptions import IconNotFoundError

    with pytest.raises(IconNotFoundError) as exc_info:
        load_local_svg("icons/does-not-exist.svg")

    assert "SVG file not found" in str(exc_info.value)
    assert "icons/does-not-exist.svg" in str(exc_info.value)


def test_local_svg_with_invalid_content_fails():
    """Test that local SVG files with invalid content fail loudly."""
    import pytest
    from pathlib import Path
    import tempfile
    from includecontents.icons.exceptions import IconBuildError

    # Create a temporary invalid SVG file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".svg", dir="tests/static/icons", delete=False
    ) as f:
        f.write("This is not valid SVG content")
        temp_path = f.name

    try:
        svg_filename = Path(temp_path).name
        with pytest.raises(IconBuildError) as exc_info:
            load_local_svg(f"icons/{svg_filename}")

        assert "Invalid SVG content" in str(exc_info.value)
    finally:
        # Clean up
        Path(temp_path).unlink()
