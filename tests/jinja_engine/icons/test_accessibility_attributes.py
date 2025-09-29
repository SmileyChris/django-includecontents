"""
Test accessibility attributes for icons in Jinja templates.
Tests that icons properly handle aria-* and role attributes.
"""

from unittest.mock import patch
from jinja2 import Environment, DictLoader

from includecontents.jinja2.extension import IncludeContentsExtension


def mock_iconify_fetch():
    """Mock function that returns test icon data."""

    def mock_fetch_fn(
        prefix, icon_names, api_base, cache_root=None, cache_static_path=None
    ):
        return {
            "home": {"body": '<path d="M10 10"/>', "viewBox": "0 0 24 24"},
            "user": {"body": '<circle cx="12" cy="12" r="3"/>', "viewBox": "0 0 24 24"},
        }

    return mock_fetch_fn


def create_jinja_env():
    """Create Jinja environment with icon extension."""
    loader = DictLoader({})
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_aria_label(mock_fetch):
    """Test that aria-label is properly applied to icons in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = '<icon:home aria-label="Home page" class="nav-icon" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should include accessibility attributes and render icon
    assert "Home page" in result  # Accessibility text preserved
    assert "nav-icon" in result  # CSS class preserved
    assert "<svg" in result  # Icon renders as SVG
    assert "#home" in result  # Icon reference included


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_aria_hidden(mock_fetch):
    """Test that aria-hidden attribute works with icons in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = '<icon:user aria-hidden="true" class="decorative" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should include aria-hidden in the SVG element (should preserve hyphens like Django)
    assert 'aria-hidden="true"' in result
    assert 'class="decorative"' in result
    assert (
        "<svg" in result
        and 'aria-hidden="true"' in result
        and 'class="decorative"' in result
    )


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_role_attribute(mock_fetch):
    """Test that role attribute is properly applied to icons in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = '<icon:home role="img" aria-label="Navigation" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should include role attribute in the SVG element
    assert 'role="img"' in result
    assert 'aria-label="Navigation"' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_multiple_aria_attributes(mock_fetch):
    """Test multiple aria attributes on icons in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = '<icon:user aria-label="User profile" aria-describedby="user-help" role="button" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should include all aria attributes (should preserve hyphens like Django)
    assert 'aria-label="User profile"' in result
    assert 'aria-describedby="user-help"' in result
    assert 'role="button"' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_accessibility_with_template_variables(mock_fetch):
    """Test accessibility attributes with template variables in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = (
        '<icon:home aria-label="{{ icon_label }}" role="{{ icon_role }}" />'
    )
    template = env.from_string(template_source)
    result = template.render(icon_label="Go home", icon_role="link")

    # Template variables should be processed in accessibility attributes
    assert 'aria-label="Go home"' in result
    assert 'role="link"' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_conditional_accessibility_attributes(mock_fetch):
    """Test conditional accessibility attributes in Jinja."""
    mock_fetch.side_effect = mock_iconify_fetch()

    env = create_jinja_env()
    template_source = '<icon:home {% if is_decorative %}aria-hidden="true"{% else %}aria-label="Home"{% endif %} />'
    template = env.from_string(template_source)

    # Test decorative case
    result1 = template.render(is_decorative=True)
    assert 'aria-hidden="true"' in result1

    # Test labeled case
    result2 = template.render(is_decorative=False)
    assert 'aria-label="Home"' in result2


if __name__ == "__main__":
    # Run a quick test
    test_jinja_icon_aria_label()
    print("✅ Jinja icon accessibility tests created successfully")
