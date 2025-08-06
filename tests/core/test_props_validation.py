import pytest
from django.template import Context, TemplateSyntaxError
from django.template.loader import render_to_string

from includecontents.django.base import Template


def test_enum_required():
    """Test that required enum props must be provided."""
    with pytest.raises(
        TemplateSyntaxError,
        match='Missing required attribute "variant" in <include:button>',
    ):
        Template(
            '<include:button>Click me</include:button>'
        ).render(Context())


def test_enum_invalid_value():
    """Test that invalid enum values are rejected."""
    with pytest.raises(
        TemplateSyntaxError,
        match=r'Invalid value "invalid" for attribute "variant" in <include:button>\. Allowed values: \'primary\', \'secondary\', \'accent\'',
    ):
        Template(
            '<include:button variant="invalid">Click me</include:button>'
        ).render(Context())


def test_enum_valid_value():
    """Test that valid enum values work correctly."""
    output = Template(
        '<include:button variant="primary">Click me</include:button>'
    ).render(Context())
    assert 'class="btn btn-primary"' in output
    assert '>Click me<' in output


def test_enum_optional():
    """Test that optional enum props work when not provided."""
    output = Template(
        '<include:button-optional>Click me</include:button-optional>'
    ).render(Context())
    assert 'class="btn"' in output
    assert '>Click me<' in output


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
    assert '>Click me<' in output


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