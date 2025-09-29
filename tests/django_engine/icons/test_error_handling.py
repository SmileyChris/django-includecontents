"""
Test that icon build failures fail loudly.
"""

import pytest
from unittest.mock import patch
from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons.builder import get_or_create_sprite
from includecontents.icons.finders import IconSpriteFinder
from includecontents.icons.exceptions import (
    IconConfigurationError,
    IconNotFoundError,
    IconBuildError,
    IconAPIError,
)


def test_invalid_icon_name_fails_loudly():
    """Test that invalid icon names cause loud failures during validation."""
    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": ["invalid-icon-without-prefix"],  # Missing prefix like 'mdi:'
        }
    ):
        with pytest.raises(IconConfigurationError) as exc_info:
            get_or_create_sprite()

        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value)
        assert "Invalid icon name" in str(exc_info.value)


def test_nonexistent_local_svg_fails_loudly():
    """Test that nonexistent local SVG files cause loud failures."""
    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": ["icons/does-not-exist.svg"],
        }
    ):
        with pytest.raises(IconNotFoundError) as exc_info:
            get_or_create_sprite()

        assert "SVG file not found" in str(exc_info.value)
        assert "does-not-exist.svg" in str(exc_info.value)


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_iconify_api_failure_fails_loudly(mock_fetch):
    """Test that Iconify API failures cause loud failures."""
    mock_fetch.side_effect = IconAPIError("API connection failed")

    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": ["mdi:home"],
        }
    ):
        with pytest.raises(IconAPIError) as exc_info:
            get_or_create_sprite()

        assert "API connection failed" in str(exc_info.value)


def test_template_tag_propagates_build_errors():
    """Test that template tags let build errors bubble up."""
    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": ["invalid-icon-without-prefix"],
        }
    ):
        template_str = '{% icon "home" %}'
        template = CustomTemplate(template_str)

        # The template rendering should raise the validation error
        with pytest.raises(IconConfigurationError) as exc_info:
            template.render(Context())

        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value)


def test_collectstatic_fails_on_sprite_error():
    """Test that collectstatic fails loudly on sprite generation errors."""
    with override_settings(
        INCLUDECONTENTS_ICONS={
            "icons": ["invalid-icon-without-prefix"],
        }
    ):
        finder = IconSpriteFinder()

        # The list() method should raise an error during collectstatic
        # The validation error is now an IconBuildError
        with pytest.raises(IconBuildError) as exc_info:
            list(finder.list([]))

        assert "Invalid INCLUDECONTENTS_ICONS configuration" in str(exc_info.value)
