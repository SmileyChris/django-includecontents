import pytest
from django.template import Context, TemplateSyntaxError

from includecontents.django.base import Template


def test_enum_required():
    """Test that required enum props must be provided."""
    with pytest.raises(
        TemplateSyntaxError,
        match='Missing required attribute "variant" in <include:button>',
    ):
        Template("<include:button>Click me</include:button>").render(Context())


def test_enum_invalid_value():
    """Test that invalid enum values are rejected."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "invalid" for attribute "variant" in <include:button>\. Allowed values: \'primary\', \'secondary\', \'accent\'',
    ):
        Template('<include:button variant="invalid">Click me</include:button>').render(
            Context()
        )


def test_enum_valid_value():
    """Test that valid enum values work correctly."""
    output = Template(
        '<include:button variant="primary">Click me</include:button>'
    ).render(Context())
    assert 'class="btn btn-primary"' in output
    assert ">Click me<" in output


def test_enum_optional():
    """Test that optional enum props work when not provided."""
    output = Template(
        "<include:button-optional>Click me</include:button-optional>"
    ).render(Context())
    assert 'class="btn"' in output
    assert ">Click me<" in output


def test_enum_optional_with_value():
    """Test that optional enum props accept valid values."""
    output = Template(
        '<include:button-optional variant="secondary">Click me</include:button-optional>'
    ).render(Context())
    assert 'class="btn btn-secondary"' in output


def test_enum_empty_value_allowed():
    """Test that empty string is allowed if it's in the enum list."""
    output = Template(
        '<include:button-optional variant="">No variant</include:button-optional>'
    ).render(Context())
    assert 'class="btn"' in output


def test_enum_with_hyphens():
    """Test enum values that contain hyphens get camelCased."""
    output = Template(
        '<include:button-optional variant="dark-mode">Dark mode</include:button-optional>'
    ).render(Context())
    assert 'class="btn btn-dark-mode"' in output


def test_enum_multiple_values():
    """Test that multiple enum values can be specified."""
    output = Template(
        '<include:button-multi variant="primary icon">Click me</include:button-multi>'
    ).render(Context())
    assert 'class="btn btn-primary btn-icon"' in output
    assert ">Click me<" in output


def test_enum_multiple_values_validation():
    """Test that all values in a multi-value enum are validated."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "invalid" for attribute "variant" in <include:button-multi>\. Allowed values: \'primary\', \'secondary\', \'accent\', \'icon\', \'large\'',
    ):
        Template(
            '<include:button-multi variant="primary invalid">Click me</include:button-multi>'
        ).render(Context())


def test_enum_multiple_values_with_hyphens():
    """Test multiple enum values with hyphens."""
    output = Template(
        '<include:button-optional variant="dark-mode icon-only">Icon</include:button-optional>'
    ).render(Context())
    assert 'class="btn btn-dark-mode btn-icon-only"' in output


def test_enum_with_special_characters():
    """Test enum values containing special characters."""
    output = Template(
        '<include:enum-edge-cases special="@">Special</include:enum-edge-cases>'
    ).render(Context())
    assert 'data-special="@"' in output


def test_enum_with_numbers():
    """Test enum values that are numbers."""
    output = Template(
        '<include:enum-edge-cases numbers="1">Number</include:enum-edge-cases>'
    ).render(Context())
    assert 'data-numbers="1"' in output


def test_enum_invalid_special_character():
    """Test that invalid special characters are rejected."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "&" for attribute "special" in <include:enum-edge-cases>\. Allowed values: \'@\', \'#\', \'\$\', \'%\'',
    ):
        Template(
            '<include:enum-edge-cases special="&">Invalid</include:enum-edge-cases>'
        ).render(Context())


def test_enum_empty_definition():
    """Test component with empty enum definition."""
    # Empty enum should not be treated as enum
    output = Template(
        '<include:enum-empty variant="anything">Empty</include:enum-empty>'
    ).render(Context())
    assert 'class="empty-enum"' in output


def test_enum_whitespace_handling():
    """Test that enum definitions with whitespace are handled correctly."""
    output = Template(
        '<include:enum-whitespace variant="a">Whitespace</include:enum-whitespace>'
    ).render(Context())
    assert 'data-variant="a"' in output


def test_enum_invalid_whitespace_value():
    """Test that invalid values in whitespace enum are rejected."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "invalid" for attribute "variant" in <include:enum-whitespace>\. Allowed values: \'a\', \'b\', \'c\'',
    ):
        Template(
            '<include:enum-whitespace variant="invalid">Invalid</include:enum-whitespace>'
        ).render(Context())


def test_enum_mixed_empty_values():
    """Test enum definition with mixed content and empty values."""
    output = Template(
        '<include:enum-edge-cases mixed="test">Mixed</include:enum-edge-cases>'
    ).render(Context())
    assert 'data-mixed="test"' in output


def test_enum_single_character():
    """Test enum with single character value."""
    output = Template(
        '<include:enum-edge-cases single="a">Single</include:enum-edge-cases>'
    ).render(Context())
    assert 'data-single="a"' in output


def test_enum_case_sensitivity():
    """Test that enum validation is case-sensitive."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "PRIMARY" for attribute "variant" in <include:button>\. Allowed values: \'primary\', \'secondary\', \'accent\'',
    ):
        Template(
            '<include:button variant="PRIMARY">Case sensitive</include:button>'
        ).render(Context())


def test_enum_null_and_false_values():
    """Test enum handling of null and false values."""
    # Test with Django template variables that resolve to None/False
    context = Context({"none_value": None, "false_value": False, "empty_string": ""})

    # None should be treated as empty and allowed if enum is optional
    output = Template(
        '<include:button-optional variant="{{ none_value }}">None</include:button-optional>'
    ).render(context)
    assert 'class="btn"' in output

    # False should be treated as empty
    output = Template(
        '<include:button-optional variant="{{ false_value }}">False</include:button-optional>'
    ).render(context)
    assert 'class="btn"' in output

    # Empty string should work too
    output = Template(
        '<include:button-optional variant="{{ empty_string }}">Empty</include:button-optional>'
    ).render(context)
    assert 'class="btn"' in output


def test_enum_list_values():
    """Test enum handling with list/tuple values from context."""
    context = Context(
        {
            "variant_list": ["primary", "icon"],
            "variant_tuple": ("secondary", "large"),
            "variant_set": {"accent"},
        }
    )

    # List of enum values
    output = Template(
        '<include:button-multi variant="{{ variant_list }}">List</include:button-multi>'
    ).render(context)
    assert 'class="btn btn-primary btn-icon"' in output

    # Tuple of enum values
    output = Template(
        '<include:button-multi variant="{{ variant_tuple }}">Tuple</include:button-multi>'
    ).render(context)
    assert 'class="btn btn-secondary btn-large"' in output

    # Set of enum values
    output = Template(
        '<include:button-multi variant="{{ variant_set }}">Set</include:button-multi>'
    ).render(context)
    assert 'class="btn btn-accent"' in output


def test_enum_mixed_list_with_invalid():
    """Test that invalid values in lists are caught."""
    context = Context({"invalid_list": ["primary", "invalid", "secondary"]})

    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "invalid" for attribute "variant" in <include:button-multi>\. Allowed values: \'primary\', \'secondary\', \'accent\', \'icon\', \'large\'',
    ):
        Template(
            '<include:button-multi variant="{{ invalid_list }}">Invalid list</include:button-multi>'
        ).render(context)
