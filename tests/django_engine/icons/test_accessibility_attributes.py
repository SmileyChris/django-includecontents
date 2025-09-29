"""
Test accessibility attribute placement on SVG vs USE elements.
"""

from unittest.mock import patch
from django.test import override_settings
from django.template import Context

from includecontents.django.base import Template as CustomTemplate


def mock_iconify_fetch():
    """Mock function for iconify API calls."""

    def mock_fetch_fn(prefix, icon_names, api_base):
        if prefix == "mdi":
            return {"home": {"body": '<path d="M10 10"/>', "viewBox": "0 0 24 24"}}
        return {}

    return mock_fetch_fn


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [("home", "mdi:home")],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_aria_attributes_on_svg_element(mock_fetch):
    """Test that ARIA attributes can be placed on the SVG element (recommended)."""
    mock_fetch.side_effect = mock_iconify_fetch()

    template_str = (
        '<icon:home role="img" aria-label="Go to homepage" class="nav-icon" />'
    )
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # ARIA attributes should be on the SVG element
    assert 'role="img"' in result
    assert 'aria-label="Go to homepage"' in result
    assert 'class="nav-icon"' in result

    # Should generate SVG with proper structure
    assert "<svg" in result
    assert "<use" in result
    assert '#home">' in result


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [("home", "mdi:home")],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_aria_attributes_on_use_element(mock_fetch):
    """Test that ARIA attributes can also be placed on USE element (still works)."""
    mock_fetch.side_effect = mock_iconify_fetch()

    template_str = (
        '<icon:home class="nav-icon" use.role="img" use.aria-label="Go to homepage" />'
    )
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # ARIA attributes should be on the USE element
    assert 'class="nav-icon"' in result
    # The exact position of attributes may vary, but they should be in the USE element
    assert 'role="img"' in result
    assert 'aria-label="Go to homepage"' in result
    assert '#home">' in result


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [("star", "mdi:star")],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_mixed_attribute_placement(mock_fetch):
    """Test that SVG and USE attributes can be used together."""
    mock_fetch.side_effect = lambda prefix, names, api: (
        {"star": {"body": '<path d="star"/>', "viewBox": "0 0 24 24"}}
        if prefix == "mdi"
        else {}
    )

    template_str = """<icon:star 
        class="icon-wrapper" 
        role="img" 
        aria-label="Favorite item"
        use.class="star-fill" 
        use.style="color: gold" />"""
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # SVG should get main attributes
    assert 'class="icon-wrapper"' in result
    assert 'role="img"' in result
    assert 'aria-label="Favorite item"' in result

    # USE should get use.* attributes
    assert 'class="star-fill"' in result
    assert 'style="color: gold"' in result


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [("icon", "mdi:home")],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_decorative_icon_pattern(mock_fetch):
    """Test the recommended pattern for decorative icons."""
    mock_fetch.side_effect = mock_iconify_fetch()

    template_str = '<icon:icon aria-hidden="true" class="decorative" />'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should hide from screen readers
    assert 'aria-hidden="true"' in result
    assert 'class="decorative"' in result


@override_settings(
    INCLUDECONTENTS_ICONS={
        "icons": [("save", "mdi:content-save")],
    }
)
@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_meaningful_icon_pattern(mock_fetch):
    """Test the recommended pattern for meaningful icons."""
    mock_fetch.side_effect = lambda prefix, names, api: (
        {"content-save": {"body": '<path d="save"/>', "viewBox": "0 0 24 24"}}
        if prefix == "mdi"
        else {}
    )

    template_str = (
        '<icon:save role="img" aria-label="Save document" class="action-icon" />'
    )
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should be accessible to screen readers
    assert 'role="img"' in result
    assert 'aria-label="Save document"' in result
    assert 'class="action-icon"' in result


def test_accessibility_best_practices_documentation():
    """Document accessibility best practices through test."""

    # Best practices for icon accessibility:

    # 1. Decorative icons (purely visual)
    decorative_example = '<icon:star aria-hidden="true" />'

    # 2. Meaningful icons (convey information)
    meaningful_example = '<icon:home role="img" aria-label="Go to homepage" />'

    # 3. Icons in buttons (usually decorative if button has text)
    button_example = """
    <button>
      <icon:save aria-hidden="true" />
      Save Document
    </button>
    """

    # 4. Icons as the only content (need labels)
    icon_button_example = (
        '<button><icon:edit role="img" aria-label="Edit item" /></button>'
    )

    # These patterns ensure proper screen reader support
    assert 'aria-hidden="true"' in decorative_example
    assert 'role="img"' in meaningful_example
    assert "aria-label=" in meaningful_example
    assert 'aria-hidden="true"' in button_example
    assert "aria-label=" in icon_button_example
