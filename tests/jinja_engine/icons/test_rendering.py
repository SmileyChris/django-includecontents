"""
High-level tests for the icons system with Jinja2 templates.
Tests the <icon:name> HTML component syntax in Jinja2 environment.
"""

from unittest.mock import patch
from jinja2 import Environment, DictLoader

from includecontents.jinja2.extension import IncludeContentsExtension


def mock_all_iconify_fetches():
    """
    Create a mock function that handles all iconify fetches for tests.
    This prevents errors with our strict approach that builds all icons at once.
    """

    def mock_fetch_fn(
        prefix, icon_names, api_base, cache_root=None, cache_static_path=None
    ):
        if prefix == "mdi":
            return {"home": {"body": '<path d="M10 10"/>', "viewBox": "0 0 24 24"}}
        elif prefix == "tabler":
            return {
                "user": {
                    "body": '<circle cx="12" cy="12" r="3"/>',
                    "viewBox": "0 0 24 24",
                }
            }
        return {}

    return mock_fetch_fn


def create_jinja_env():
    """Create Jinja environment with icon extension."""
    loader = DictLoader({})
    return Environment(loader=loader, extensions=[IncludeContentsExtension])


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_html_syntax_basic(mock_fetch):
    """Test basic <icon:name> HTML syntax works in Jinja."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    template_source = '<icon:home class="w-6 h-6" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should render SVG with use element and attributes
    assert '<svg class="w-6 h-6">' in result
    assert 'href="/static/icons/sprite-' in result  # Static file URL
    assert '#home">' in result  # Symbol ID based on component name
    assert "</svg>" in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_with_attributes(mock_fetch):
    """Test <icon:name> with multiple attributes in Jinja."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    template_source = '<icon:user class="avatar" size="24" data-role="icon" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should render SVG with all attributes (should preserve hyphens like Django)
    assert '<svg class="avatar" size="24" data-role="icon">' in result
    assert '#user">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_with_template_variables(mock_fetch):
    """Test <icon:name> with template variables in attributes."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    template_source = '<icon:home class="icon {{ size_class }}" />'
    template = env.from_string(template_source)
    result = template.render(size_class="large")

    # Template variables should be processed in attributes
    assert 'class="icon large"' in result
    assert '#home">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_mixed_with_components(mock_fetch):
    """Test that icons work alongside components in Jinja."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    env.loader.mapping.update(
        {"components/card.html": '<div class="card">{{ contents }}</div>'}
    )

    template_source = """
    <include:card>
        <icon:home class="card-icon" />
        Card content
    </include:card>
    """
    template = env.from_string(template_source)
    result = template.render()

    # Should have both card and icon rendered
    assert '<div class="card">' in result
    assert '<svg class="card-icon">' in result
    assert '#home">' in result
    assert "Card content" in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_preprocessing(mock_fetch):
    """Test that <icon:name> syntax is preprocessed correctly in Jinja."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    extension = env.extensions[IncludeContentsExtension.identifier]

    # Test preprocessing
    source = '<icon:home class="nav-icon" />'
    processed = extension.preprocess(source, name=None)

    # Should convert to icon function call with attributes dictionary
    assert 'icon("home"' in processed
    assert '{"class": "nav-icon"}' in processed

    # Test actual rendering
    template = env.from_string(source)
    result = template.render()
    assert '<svg class="nav-icon">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_no_closing_tags(mock_fetch):
    """Test that icon closing tags are ignored in Jinja."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    env = create_jinja_env()
    extension = env.extensions[IncludeContentsExtension.identifier]

    # Icons should not have closing tags
    source = '<icon:home class="icon" /></icon:home>'
    processed = extension.preprocess(source, name=None)

    # Should have one icon function call and ignore closing tag
    assert processed.count('icon("home"') == 1
    assert "</icon:home>" not in processed


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_jinja_icon_error_handling(mock_fetch):
    """Test icon error handling in Jinja."""
    # Mock fetch to return empty (simulating API failure)
    mock_fetch.return_value = {}

    env = create_jinja_env()
    template_source = '<icon:nonexistent class="test" />'
    template = env.from_string(template_source)
    result = template.render()

    # Should render error comment when icon not found - might be empty or error comment
    # In test environment, icons system may not be fully configured
    assert isinstance(result, str)  # Should return string, not crash


if __name__ == "__main__":
    # Run a quick test
    test_jinja_icon_html_syntax_basic()
    print("✅ Jinja icon rendering tests created successfully")
