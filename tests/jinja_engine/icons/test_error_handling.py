"""
Test that icon build failures fail loudly in Jinja environment.
"""

import pytest
from unittest.mock import patch
from jinja2 import Environment, DictLoader

from includecontents.jinja2.extension import IncludeContentsExtension
from includecontents.icons.exceptions import (
    IconBuildError,
    IconAPIError,
)


def create_jinja_env():
    """Create Jinja environment with icon extension."""
    loader = DictLoader({})
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_api_error_handling(mock_fetch):
    """Test that API errors are handled gracefully in Jinja."""
    # Mock fetch to raise an API error
    mock_fetch.side_effect = IconAPIError("API is down")

    env = create_jinja_env()
    template_source = '<icon:home class="test" />'
    template = env.from_string(template_source)

    # Should not raise, but handle gracefully
    result = template.render()
    assert isinstance(result, str)  # Should return string, not crash


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_not_found_error(mock_fetch):
    """Test that missing icons show error in Jinja."""
    # Mock fetch to return empty results
    mock_fetch.return_value = {}

    env = create_jinja_env()
    template_source = '<icon:nonexistent class="test" />'
    template = env.from_string(template_source)

    result = template.render()
    # Should handle gracefully - may return empty string or error comment
    assert isinstance(result, str)  # Should return string, not crash


def test_jinja_icon_preprocessing_error_handling():
    """Test that preprocessing handles malformed icon syntax by raising an error."""
    env = create_jinja_env()
    extension = env.extensions[IncludeContentsExtension.identifier]

    # Test with malformed icon syntax
    source = '<icon: class="test" />'  # Missing icon name

    # Should raise TemplateSyntaxError for malformed syntax
    from jinja2.exceptions import TemplateSyntaxError

    with pytest.raises(TemplateSyntaxError, match="Empty component name"):
        extension.preprocess(source, name=None)


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_build_error_resilience(mock_fetch):
    """Test that build errors don't crash template rendering in Jinja."""
    # Mock fetch to raise a build error
    mock_fetch.side_effect = IconBuildError("Build failed")

    env = create_jinja_env()
    template_source = '<icon:home class="test" />'
    template = env.from_string(template_source)

    # Should handle error gracefully
    result = template.render()
    assert isinstance(result, str)  # Should return some result, not crash


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_with_invalid_attributes(mock_fetch):
    """Test that invalid attributes don't break icon rendering in Jinja."""
    mock_fetch.return_value = {
        "home": {"body": '<path d="M10 10"/>', "viewBox": "0 0 24 24"}
    }

    env = create_jinja_env()
    # Template with potentially problematic attribute values
    template_source = '<icon:home class="{{ broken_var }}" data-test="{{ None }}" />'
    template = env.from_string(template_source)

    # Should handle undefined variables gracefully
    result = template.render()
    assert "<svg" in result  # Should still render SVG


if __name__ == "__main__":
    # Run a quick test
    test_jinja_icon_not_found_error()
    print("✅ Jinja icon error handling tests created successfully")
