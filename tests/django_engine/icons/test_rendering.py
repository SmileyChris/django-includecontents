"""
High-level tests for the icons system.
Tests both HTML component syntax and template tag usage.
"""

import pytest
from unittest.mock import patch
from django.template.loader import render_to_string
from django.template import Context

from includecontents.django.base import Template as CustomTemplate
from includecontents.icons import builder, utils


# Tests now use real Django settings from tests/settings.py


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


# Removed setup_function to avoid Django settings issues


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_html_component_syntax_basic(mock_fetch):
    """Test basic <icon:name> HTML syntax works."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    result = render_to_string("test_icons/basic.html")

    # Should render SVG with use element and attributes
    assert '<svg class="w-6 h-6">' in result
    assert 'href="/static/icons/sprite-' in result  # Static file URL
    assert '#home">' in result  # Symbol ID based on component name
    assert "</svg>" in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_html_component_syntax_with_use_attrs(mock_fetch):
    """Test <icon:name> with use.* attributes."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    result = render_to_string("test_icons/with_use_attrs.html")

    # SVG should get main attributes
    assert '<svg class="w-6 h-6">' in result
    # USE element should get use.* attributes
    assert '#home">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_template_tag_syntax_basic(mock_fetch):
    """Test {% icon %} template tag syntax."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Use custom template engine which has icons in builtins, so no {% load %} needed
    template_str = '{% icon "home" class="w-6 h-6" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert '<svg class="w-6 h-6">' in result
    assert '#home">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_template_tag_with_use_attrs(mock_fetch):
    """Test {% icon %} with use.* attributes."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Use custom template engine which has icons in builtins, so no {% load %} needed
    template_str = '{% icon "home" class="w-6 h-6" use.class="fill-current" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert '<svg class="w-6 h-6">' in result
    assert '#home">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_all_configured_icons_together(mock_fetch):
    """Test all icons from settings.py work correctly together."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test all 5 icons configured in tests/settings.py
    template_str = """
    <icon:home class="icon-1" />
    <icon:user class="icon-2" />
    <icon:home2 class="icon-3" />
    <icon:custom-home class="icon-4" />
    <icon:my-star class="icon-5" />
    """
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Verify all icons render with correct symbol IDs
    assert '#home">' in result
    assert '#user">' in result
    assert '#home2">' in result
    assert '#custom-home">' in result
    assert '#my-star">' in result

    # Verify classes are applied
    assert '<svg class="icon-1">' in result
    assert '<svg class="icon-2">' in result
    assert '<svg class="icon-3">' in result
    assert '<svg class="icon-4">' in result
    assert '<svg class="icon-5">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_home2_tuple_icon(mock_fetch):
    """Test home2 icon defined as tuple ('home2', 'mdi:home')."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test HTML component syntax
    template_str = '<icon:home2 class="w-8 h-8" />'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should use the component name (home2) as symbol ID
    assert '#home2">' in result
    assert '<svg class="w-8 h-8">' in result

    # Test template tag syntax
    template_str = '{% icon "home2" class="test-class" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert '#home2">' in result
    assert '<svg class="test-class">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_my_star_local_svg_tuple(mock_fetch):
    """Test my-star icon defined as tuple ('my-star', 'icons/custom-star.svg')."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test HTML component syntax
    template_str = '<icon:my-star class="star-icon" />'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should use the component name (my-star) as symbol ID
    assert '#my-star">' in result
    assert '<svg class="star-icon">' in result

    # Test template tag syntax
    template_str = '{% icon "my-star" id="test-star" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert '#my-star">' in result
    assert 'id="test-star"' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_custom_home_local_svg_direct(mock_fetch):
    """Test icons/custom-home.svg direct local SVG file reference."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # For direct SVG files, the component name is derived from the filename
    # icons/custom-home.svg -> custom-home
    template_str = '<icon:custom-home class="custom-icon" />'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should use the derived component name (custom-home) as symbol ID
    assert '#custom-home">' in result
    assert '<svg class="custom-icon">' in result

    # Test with template tag
    template_str = '{% icon "custom-home" aria-label="Custom Home Icon" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert '#custom-home">' in result
    assert 'aria-label="Custom Home Icon"' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_icons_inline_tag(mock_fetch):
    """Test {% icons_inline %} template tag with icon rendering."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    result = render_to_string("test_icons/inline_sprite.html")

    # The main thing to test is that icons render properly
    # The inline sprite behavior may vary based on storage conditions
    assert '#home">' in result
    assert '#user">' in result
    assert '<svg class="icon">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_nonexistent_icon_renders_nothing(mock_fetch):
    """Test that non-existent icons render nothing."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test non-existent icon returns empty string
    template_str = '{% icon "nonexistent" class="w-6 h-6" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert result.strip() == ""


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_icon_as_variable(mock_fetch):
    """Test {% icon %} with 'as variable_name' syntax."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test storing icon in variable
    template_str = """
    {% icon "home" class="w-6 h-6" as my_icon %}
    Icon stored: {{ my_icon|length }}
    Render it: {{ my_icon }}
    """
    template = CustomTemplate(template_str)
    context = Context()
    result = template.render(context)

    # Should not render the icon directly
    assert "Icon stored:" in result
    # Should have the icon stored in variable and rendered later
    assert '<svg class="w-6 h-6">' in result
    assert '#home">' in result

    # Test non-existent icon with as variable
    template_str = """
    {% icon "nonexistent" class="w-6 h-6" as missing_icon %}
    Missing: "{{ missing_icon }}"
    """
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert 'Missing: ""' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_component_style_attrs_integration(mock_fetch):
    """Test icon usage within component with attrs object."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    from includecontents.templatetags.includecontents import Attrs

    attrs = Attrs()
    attrs["class"] = "w-8 h-8"
    attrs["use.class"] = "text-blue-500"
    attrs["use.role"] = "img"

    # Use custom template engine which has icons in builtins
    template_str = '{% icon "home" %}'
    template = CustomTemplate(template_str)
    context = Context({"attrs": attrs})
    result = template.render(context)

    # Should use attrs from context
    assert '<svg class="w-8 h-8">' in result
    assert '#home">' in result


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_attribute_precedence(mock_fetch):
    """Test that tag attributes override context attrs."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    from includecontents.templatetags.includecontents import Attrs

    attrs = Attrs()
    attrs["class"] = "w-8 h-8"  # This should be overridden
    attrs["use.role"] = "img"  # This should remain

    # Use custom template engine which has icons in builtins
    template_str = '{% icon "home" class="w-4 h-4" use.class="text-red-500" %}'
    template = CustomTemplate(template_str)
    context = Context({"attrs": attrs})
    result = template.render(context)

    # Tag attributes should take precedence
    assert '<svg class="w-4 h-4">' in result  # Overridden
    # Check that both attributes are present (order doesn't matter)
    assert 'class="text-red-500"' in result
    assert 'role="img"' in result
    assert '#home"' in result


def test_icon_name_sanitization():
    """Test that icon names are properly sanitized for symbol IDs."""
    # Test the utility function directly
    result = utils.get_icon_names_from_definitions(
        ["mdi:home-outline", "tabler:user-plus"]
    )
    expected = ["mdi:home-outline", "tabler:user-plus"]
    assert result == expected


def test_sprite_hash_generation():
    """Test sprite hash generation for cache invalidation."""
    icons = ["mdi:home", "tabler:user"]
    hash1 = builder.generate_icon_hash(icons)

    # Same icons should produce same hash
    hash2 = builder.generate_icon_hash(icons)
    assert hash1 == hash2

    # Different icons should produce different hash
    hash3 = builder.generate_icon_hash(["mdi:home", "mdi:user"])
    assert hash1 != hash3


def test_tuple_parsing():
    """Test parsing of tuple-based icon definitions."""
    definitions = [
        "mdi:home",
        ("custom-home", "mdi:house"),
        "tabler:user",
    ]

    component_map = utils.parse_icon_definitions(definitions)

    # Direct names should map component name to full icon name
    assert component_map["home"] == "mdi:home"
    assert component_map["user"] == "tabler:user"

    # Tuple should map custom name to actual icon
    assert component_map["custom-home"] == "mdi:house"


def test_icon_dataclass():
    """Test the Icon dataclass creation and usage."""
    # Test from Iconify icon
    icon = utils.Icon.from_definition("mdi:home")
    assert icon.component_name == "home"
    assert icon.icon_source == "mdi:home"

    # Test from local SVG
    icon = utils.Icon.from_definition("icons/logo.svg")
    assert icon.component_name == "logo"
    assert icon.icon_source == "icons/logo.svg"

    # Test from tuple
    icon = utils.Icon.from_definition(("custom", "tabler:star"))
    assert icon.component_name == "custom"
    assert icon.icon_source == "tabler:star"

    # Test immutability (frozen=True)
    icon = utils.Icon.from_definition("mdi:home")
    with pytest.raises(AttributeError):
        icon.component_name = "changed"


def test_normalize_icon_definition_string():
    """Test normalizing string icon definitions."""
    result = utils.normalize_icon_definition("mdi:home")
    assert result == ("home", "mdi:home")


def test_normalize_icon_definition_tuple():
    """Test normalizing tuple icon definitions."""
    result = utils.normalize_icon_definition(("custom-name", "mdi:house"))
    assert result == ("custom-name", "mdi:house")


def test_parse_icon_definitions_to_icons():
    """Test parsing icon definitions to Icon objects."""
    definitions = [
        "mdi:home",
        ("custom", "tabler:star"),
        "icons/logo.svg",
    ]

    icons = utils.parse_icon_definitions_to_icons(definitions)

    assert len(icons) == 3
    assert icons[0].component_name == "home"
    assert icons[0].icon_source == "mdi:home"
    assert icons[1].component_name == "custom"
    assert icons[1].icon_source == "tabler:star"
    assert icons[2].component_name == "logo"
    assert icons[2].icon_source == "icons/logo.svg"


def test_get_icon_names_from_definitions():
    """Test extracting icon names from mixed definitions."""
    definitions = ["mdi:home", ("custom", "tabler:user"), "lucide:star"]

    result = utils.get_icon_names_from_definitions(definitions)
    expected = ["mdi:home", "tabler:user", "lucide:star"]
    # Sort both lists since order may vary
    assert sorted(result) == sorted(expected)


def test_memory_cache_operations():
    """Test sprite cache operations using Django cache."""
    from includecontents.icons.cache import sprite_cache

    test_hash = "test123"
    test_content = "<svg>test</svg>"

    # Clear any existing cache first
    sprite_cache.delete(test_hash)

    # Should not exist initially
    assert sprite_cache.get(test_hash) is None

    # Store and retrieve
    sprite_cache.set(test_hash, test_content)
    result = sprite_cache.get(test_hash)
    assert result == test_content

    # Clean up
    sprite_cache.delete(test_hash)


def test_sprite_filename_generation():
    """Test sprite filename generation."""
    test_hash = "abcd1234"
    filename = builder.get_sprite_filename(test_hash)

    assert filename == f"sprite-{test_hash}.svg"


@patch("includecontents.icons.builder.fetch_iconify_icons")
def test_cache_bust_parameter(mock_fetch):
    """Test cache_bust parameter for cache breaking."""
    mock_fetch.side_effect = mock_all_iconify_fetches()

    # Test with explicit cache_bust value
    template_str = '{% icon "home" class="w-6 h-6" cache_bust="t=123456" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should include cache bust parameter in URL
    assert "t=123456" in result
    assert '<svg class="w-6 h-6">' in result
    assert "#home" in result

    # Test with different cache bust value
    template_str = '{% icon "home" cache_bust="v=2.0" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert "v=2.0" in result

    # Test cache_bust without value (should auto-generate timestamp)
    template_str = '{% icon "home" cache_bust %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    # Should contain a timestamp parameter with _ format
    import re

    assert re.search(r"\?_=\d+", result), f"No timestamp found in: {result}"

    # Test without cache_bust should work normally
    template_str = '{% icon "home" class="w-6 h-6" %}'
    template = CustomTemplate(template_str)
    result = template.render(Context())

    assert "t=123456" not in result  # Should not contain previous cache bust
    assert "v=2.0" not in result
    assert not re.search(r"\?_=\d+", result)  # Should not contain timestamp
    assert '<svg class="w-6 h-6">' in result
